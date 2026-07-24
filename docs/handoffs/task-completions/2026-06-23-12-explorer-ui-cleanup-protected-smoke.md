# Lane 12 - Explorer UI Cleanup Protected Smoke

## Pass / warn / fail

**Pass with warnings.**

Protected-preview runtime was refreshed to implementation commit `e1103be`, and authenticated browser smoke completed through Cloudflare Access for the main app, Explorer route, SVG asset route, and regression prompt matrix.

Warnings:

- Main header backstage action is functional and targets `aria-controls="backstage"`, but visible label is `Get a Backstage Pass`, not `Go Backstage`.
- Browser direct navigation to `https://app.steelguitarrag.com/api/version` was blocked by the browser client with `net::ERR_BLOCKED_BY_CLIENT`; local `/api/version` confirmed runtime `e1103be`.
- Browser console recorded `Uncaught (in promise) TypeError: Cannot use 'in' operator to search for 'animation' in undefined` after Explorer select/asset smoke. It did not block page rendering or interaction, but should be reviewed by Lane 06 if it reproduces manually.

API fallback was not used as browser-smoke proof.

## Task summary

Requested:

- Refresh protected preview so it serves `e1103be fix: clean up explorer controls and key labels`.
- Verify the home header controls and Explorer cleanup through Cloudflare Access.
- Run the listed answer regression prompts.
- Preserve unrelated dirty work and avoid broad staging.

Completed:

- Confirmed current branch and HEAD.
- Confirmed runtime was stale at `1c0bbd6`.
- Restarted the launchd-supervised app by terminating stale PID `94266`; launchd restarted it as PID `50954`.
- Confirmed local `/api/version` reports `e1103be`.
- Confirmed launchd owns the listener on `127.0.0.1:8770`.
- Confirmed manual `screen` runtime is absent.
- Confirmed Cloudflare Tunnel process is running.
- Ran authenticated protected-preview browser smoke at exact cache-busted main app and Explorer URLs.
- Ran the full requested answer prompt matrix through the browser UI.

Intentionally not changed:

- No backend, UI, deployment, auth, DNS, Cloudflare Access, tunnel, corpus, Chroma/vector store, embeddings, scraper, private-source, source-inbox, or asset files were changed.
- No scraping, embedding, Chroma rebuild, or corpus work was run.

## Branch and commits

- Branch: `feature/answer-api`
- Starting HEAD: `e1103be`
- Runtime commit expected: `e1103be`
- Runtime commit reported by local `/api/version`: `e1103be`

Recent commits inspected:

```text
e1103be fix: clean up explorer controls and key labels
7f3b0fc docs: refresh smoke feedback integration status
08221a6 docs: complete smoke feedback protected preview
cc884b2 docs: record final smoke feedback protected preview
1c0bbd6 fix: separate backstage and fretboard header actions
2d3d662 fix: expose all explorer keys and backstage link
5031f43 fix: normalize accidentals and route flat-key string groupings
0c050ee fix: polish smoke feedback UI and explorer controls
3811a8c docs: refresh harmonized scale integration status
2728154 docs: record post-restart harmonized scale smoke
```

## Runtime refresh evidence

Before refresh:

- Local `/api/version`: `git_sha=1c0bbd6`
- Listener PID: `94266`
- Runtime was stale relative to HEAD `e1103be`.

Restart path:

- `kill 94266`
- LaunchDaemon `system/com.steelguitarrag.private-preview` restarted the app automatically.

After refresh:

```json
{"git_sha":"e1103be","git_branch":"feature/answer-api","server_started_at":"2026-06-23T21:25:20.927452+00:00","python_module":"steel_guitar_rag.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}
```

Listener:

```text
PID 50954
Started Tue Jun 23 16:25:20 2026
Python scripts/serve_v2_rerank_smoke.py --host 127.0.0.1 --port 8770 ...
```

LaunchDaemon:

- Service: `system/com.steelguitarrag.private-preview`
- State: running
- PID: `50954`
- Program: `/usr/local/libexec/steel-guitar-rag/run-private-preview-app.sh`
- stdout: `/Users/cory/Library/Logs/steel-guitar-rag/app.out.log`
- stderr: `/Users/cory/Library/Logs/steel-guitar-rag/app.err.log`

Manual runtime:

- `screen -ls`: no sockets.

Cloudflare Tunnel:

- `cloudflared` process was running.
- Tunnel token output was not copied into this handoff.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=e1103be`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=e1103be`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=e1103be`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; app pages loaded through the existing authenticated browser session.
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `e1103be`
- Version endpoint: `/api/version`
- Version endpoint result: local loopback reports `git_sha=e1103be`; browser direct protected `/api/version` navigation was blocked by the browser client with `net::ERR_BLOCKED_BY_CLIENT`.
- If version endpoint missing, how version is inferred: not applicable locally.
- Whether app root `/` works: yes, but it redirects to `/ui/steel-guitar-rag-mock.html` and drops the query string.
- Whether app root `/` is expected to work: yes as a convenience redirect, but not as the only cache-busted smoke target.
- Whether `/ui/steel-guitar-rag-mock.html` works: yes.
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes.
- Who should test this URL: the user and Lane 12.
- Do not test these URLs: do not treat local `127.0.0.1` or unauthenticated API fallback as protected-preview browser smoke.
- Known caveats: root drops the query string; use direct `/ui/...?...` URLs for exact smoke.

## Exact URLs tested

- Main app: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=e1103be`
- Explorer: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e1103be`
- Root: `https://app.steelguitarrag.com/?v=e1103be`
- SVG asset: `https://app.steelguitarrag.com/brand/pedal-steel-fretboard-background.svg?v=e1103be`

Root behavior:

- Root redirected to `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`.
- Query string was dropped.
- Use the direct cache-busted main app URL above for exact smoke.

## Main UI behavior

| Check | Status | Evidence |
|---|---|---|
| Cloudflare Access login | Pass | Main app loaded without Cloudflare login page. |
| Q&A/search visible | Pass | `#question` textarea present. |
| Backstage action remains settings/backstage | Warn | Button targets `aria-controls="backstage"` with class `backstage-trigger`; visible text is `Get a Backstage Pass`, not `Go Backstage`. |
| Explore Fretboard separate control | Pass | Header link text `Explore Fretboard`, class `explorer-header-link`. |
| Explore Fretboard styling close to Backstage family | Pass | Same background color, color, border radius, and padding; font size differs by 2px. |
| Explore Fretboard link target | Pass | `href="/ui/e9-fretboard-explorer.html"`. |
| Explore Fretboard click-through | Pass | Click opened `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html`. |
| Removed prompt chip `Explain this lick like a steel player would` absent | Pass | Not present. |
| Removed prompt chip `Show me a smoother turnaround` absent | Pass | Not present. |
| Large Explorer callout copy absent | Pass | `Open Fretboard Explorer` not present. |
| Brand assets load through protected app server | Pass | App images loaded with natural dimensions from protected app URLs. |
| Relevant console errors | Pass for initial main app | No main-app console errors captured. |

Visible main prompt chips:

```text
Show movement without sliding everywhere
Help me sound less mechanical
Show tasteful fills behind a singer
What should I woodshed tonight?
```

## Explorer behavior

| Check | Status | Evidence |
|---|---|---|
| Explorer loads through Cloudflare Access | Pass | `E9 Fretboard Explorer - Steel Guitar RAG`. |
| 12 combined key choices | Pass | Key selector shows 12 entries: C, C#/Db, D, D#/Eb, E, F, F#/Gb, G, G#/Ab, A, A#/Bb, B. |
| No duplicate enharmonic key entries | Pass | Enharmonics are combined in a single selector option. |
| No standalone 5&8 branch harmony option | Pass | Harmony/View selector has only `2-string harmonized scale` and `3-string diatonic harmony`. |
| 5&8 remains available in correct context | Pass | After selecting `2-string harmonized scale`, string group options include `5-8`. |
| No raw `five_eight_branch` label | Pass | Not visible. |
| Bad deterministic/source-card copy removed | Pass | `These Explorer rows are deterministic teaching data, separate from source-card answers.` absent. |
| Starter/Common/Advanced controls not confusing | Pass | No standalone confusing Starter/Common filter controls exposed; Explorer shows learner-facing group text such as `Advanced swap`. |
| No `E-lower+E-lower` | Pass | Not visible. |
| No `[object Object]` | Pass | Not visible. |
| Background SVG referenced in page | Pass | Explorer HTML references `/brand/pedal-steel-fretboard-background.svg`. |
| Relevant console errors | Warn | A console error appeared after select/asset smoke: `Cannot use 'in' operator to search for 'animation' in undefined`. It did not block UI behavior. |

2-string context after selecting `2-string harmonized scale`:

```text
All 2-string groups
3-5
5-6
6-10
4-6
3-4
5-8
```

## Brand asset routing

- Main app brand images loaded through protected app URLs with nonzero natural dimensions.
- Direct protected SVG URL loaded: `https://app.steelguitarrag.com/brand/pedal-steel-fretboard-background.svg?v=e1103be`.
- Browser confirmed an SVG document at that URL.
- Local served asset confirmed root SVG starts with `<svg ... viewBox="0 0 1600 420" ...>`.

## Prompt matrix results

| # | Prompt | Status | Evidence |
|---|---|---|---|
| 1 | `Show me an A-flat major string grouping.` | Pass | No generic fallback. Fretboard rendered. No source cards, warnings, or tab block. |
| 2 | `Show me an A♭ major string grouping.` | Pass | Same behavior as A-flat. |
| 3 | `Show me an Ab major string grouping.` | Pass | Same behavior as A-flat. |
| 4 | `Show me C♯ major on E9.` | Pass | No generic fallback. Fretboard rendered. No source cards, warnings, or tab block. |
| 5 | `Show me C# major on E9.` | Pass | Same behavior as C-sharp symbol prompt. |
| 6 | `Show me a G harmonized scale.` | Pass | Static fretboard-first answer. No tab, sources, or warning. |
| 7 | `Show me a G natural minor harmonized scale.` | Pass | Static fretboard-first answer. No tab, sources, or warning. |
| 8 | `Show me the F# diminished position in G.` | Pass | Fretboard rendered. Explicit diminished triad, not full F#m7b5. |
| 9 | `Show me the A diminished position in G minor.` | Pass | Fretboard rendered. Explicit diminished triad, not full Am7b5. |
| 10 | `Show me a G harmonized scale on strings 5 and 8.` | Pass | Static 5&8 branch answer. No tab, sources, or warning. |
| 11 | `Show me a G major grip.` | Pass | Static grip answer is fretboard-first. No rendered tab/code block and no `tab_example_event` wording observed. |
| 12 | `Show me a G to C move.` | Pass | Movement answer rendered deterministic tab plus matching fretboard. |
| 13 | `Give me the full tab for a modern copyrighted song.` | Pass | Refused safely. No source cards, warnings, rendered tab, or fretboard answer payload. |
| 14 | `What are good Fender Steel King settings?` | Pass | Gear answer rendered normally with source cards and no stale tab/fretboard payload. |

Shared prompt checks:

- No `[object Object]` appeared.
- No generic fallback appeared.
- Static grip/position answers were fretboard-first and did not show `tab_example` by default.
- Movement prompt included deterministic tab as expected.
- Copyright prompt refused/redirected safely.
- Gear prompt did not show stale tab/fretboard payload.

## Checks run

```text
git status --short
git branch --show-current
git rev-parse --short HEAD
git log -10 --oneline
git diff --name-only
git diff --cached --name-only
launchctl print system/com.steelguitarrag.private-preview
deploy/macos/install-private-preview-launchdaemon.sh status
deploy/macos/install-private-preview-launchdaemon.sh version
curl -sS http://127.0.0.1:8770/api/version || true
lsof -nP -iTCP:8770 -sTCP:LISTEN || true
ps -p "$(lsof -tiTCP:8770 -sTCP:LISTEN)" -o pid,lstart,command || true
screen -ls || true
pgrep -fl cloudflared || true
git diff --check
curl -sS 'http://127.0.0.1:8770/brand/pedal-steel-fretboard-background.svg?v=e1103be' | head -5
rg 'viewBox|<svg' public/brand/pedal-steel-fretboard-background.svg
```

Browser checks:

- Main app URL loaded through Cloudflare Access.
- Root URL redirect checked.
- Explorer header link clicked.
- Explorer direct URL loaded.
- Explorer 2-string mode selected.
- Prompt matrix submitted through UI.
- Direct protected SVG URL loaded.

Skipped / caveated:

- `deploy/macos/install-private-preview-launchdaemon.sh status` required sudo and failed in non-interactive shell.
- Browser direct `/api/version` navigation was blocked by the browser client; local `/api/version` confirmed runtime identity.

## Files changed

- Created `docs/handoffs/task-completions/2026-06-23-12-explorer-ui-cleanup-protected-smoke.md`.

No implementation files were changed.

## Risks

Risk: low to medium.

Reasons:

- Runtime is current at `e1103be`.
- Protected-preview browser smoke completed through Cloudflare Access.
- Functional UI, Explorer, prompt, and asset checks passed.
- Remaining warnings are label/console/version-navigation caveats, not runtime blockers.

## Blockers

No Lane 12 runtime/deployment blocker remains.

Potential follow-ups:

- Lane 06: review whether `Get a Backstage Pass` is the intended visible label for the backstage action when the task expected `Go Backstage`.
- Lane 06: investigate the browser console error after Explorer select/asset smoke if it reproduces manually.
- Lane 12 / Lane 06: decide whether root redirect should preserve query strings to avoid stale root smoke.

## Human decision needed

No for Lane 12 protected-preview readiness.

Optional decisions:

- Whether the label and console warnings should block user smoke or be routed as follow-up UI bugs.

## Safe-to-stage files

- `docs/handoffs/task-completions/2026-06-23-12-explorer-ui-cleanup-protected-smoke.md`

## Files that must remain unstaged

- All unrelated parked modified and untracked files.
- Backend/runtime files, tests, UI source files, deployment/launchd files, auth/DNS/Cloudflare config, tunnel files, source files, paid transcript files, or app assets.
- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, generated corpus outputs, scraper output, source-inbox raw/provenance files.
- Deployment secrets, private env files, rendered plists, tunnel tokens, tunnel credentials, `.wrangler/`, and any secrets.
- `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, generated visual assets, and unrelated UI/assets.

## Recommended next lane

Lane 01 Repo Steward.

Recommended next prompt:

```text
Lane 01: Refresh integration-status.md after Lane 12 completed Explorer UI cleanup protected-preview smoke at runtime e1103be. Record pass-with-warnings, preserve unrelated dirty work, and stage only the integration-status refresh.
```

## Commit readiness

Safe to commit as a docs-only protected-preview smoke handoff.
