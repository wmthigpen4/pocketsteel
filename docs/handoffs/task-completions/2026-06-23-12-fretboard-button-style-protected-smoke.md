# Lane 12 - Fretboard Button Style Protected Smoke

## Pass / warn / fail

**Pass with warnings.**

Protected preview was refreshed to implementation commit `fd342b9`, and authenticated browser smoke completed through Cloudflare Access for the main app, Explorer route, root redirect behavior, and focused prompt spot checks.

Warnings:

- Root `https://app.steelguitarrag.com/?v=fd342b9` redirects to `/ui/steel-guitar-rag-mock.html` and drops the query string. Use the direct cache-busted `/ui/...?...` URL for exact smoke.
- `deploy/macos/install-private-preview-launchdaemon.sh status` and `version` require sudo in this shell and failed non-interactively. `launchctl print`, listener checks, and local `/api/version` were used for runtime evidence.

API fallback was not used as browser-smoke proof.

## Task summary

Requested:

- Refresh protected preview so it serves `fd342b9 fix: match fretboard header button style`.
- Verify through Cloudflare Access that `Explore Fretboard` visually matches the Backstage/settings header button and no decorative font remains.
- Verify Explorer cleanup still loads.
- Run optional prompt spot checks.
- Preserve unrelated dirty work and avoid broad staging.

Completed:

- Confirmed current HEAD is `fd342b9`.
- Confirmed protected-preview runtime was stale at `e1103be`.
- Refreshed launchd-supervised runtime by terminating stale PID `50954`; launchd restarted the app as PID `84402`.
- Confirmed local `/api/version` reports `fd342b9`.
- Confirmed launchd owns the listener on `127.0.0.1:8770`.
- Confirmed manual `screen` runtime is absent.
- Confirmed Cloudflare Tunnel process is running.
- Ran authenticated protected-preview browser smoke at exact cache-busted main app and Explorer URLs.
- Verified the header button style fix with computed style evidence.
- Ran focused prompt spot checks through the browser UI.

Intentionally not changed:

- No backend, UI, deployment, auth, DNS, Cloudflare Access, tunnel, corpus, Chroma/vector store, embeddings, scraper, private-source, source-inbox, or asset files were changed.
- No scraping, embedding, Chroma rebuild, or corpus work was run.

## Branch and commits

- Branch: `feature/answer-api`
- Starting HEAD: `fd342b9`
- Runtime commit expected: `fd342b9`
- Runtime commit reported by local `/api/version`: `fd342b9`

Recent commits inspected:

```text
fd342b9 fix: match fretboard header button style
19d1845 docs: refresh explorer cleanup integration status
760dc73 docs: record explorer UI cleanup protected smoke
e1103be fix: clean up explorer controls and key labels
7f3b0fc docs: refresh smoke feedback integration status
08221a6 docs: complete smoke feedback protected preview
cc884b2 docs: record final smoke feedback protected preview
1c0bbd6 fix: separate backstage and fretboard header actions
2d3d662 fix: expose all explorer keys and backstage link
5031f43 fix: normalize accidentals and route flat-key string groupings
```

## Runtime refresh evidence

Before refresh:

- Local `/api/version`: `git_sha=e1103be`
- Listener PID: `50954`
- Runtime was stale relative to HEAD `fd342b9`.

Restart path:

- `kill 50954`
- LaunchDaemon `system/com.steelguitarrag.private-preview` restarted the app automatically.

After refresh:

```json
{"git_sha":"fd342b9","git_branch":"feature/answer-api","server_started_at":"2026-06-23T21:52:52.686704+00:00","python_module":"steel_guitar_rag.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}
```

Listener:

```text
PID 84402
Started Tue Jun 23 16:52:52 2026
Python scripts/serve_v2_rerank_smoke.py --host 127.0.0.1 --port 8770 ...
```

LaunchDaemon:

- Service: `system/com.steelguitarrag.private-preview`
- State: running
- PID after refresh: `84402`
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
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=fd342b9`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=fd342b9`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=fd342b9`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; app pages loaded through the authenticated browser session.
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `fd342b9`
- Version endpoint: `/api/version`
- Version endpoint result: local loopback reports `git_sha=fd342b9`, `git_branch=feature/answer-api`, `auth_provider=cloudflare_access`, `retrieval_mode=hybrid_private_first`
- If version endpoint missing, how version is inferred: not applicable locally.
- Whether app root `/` works: yes, but it redirects to `/ui/steel-guitar-rag-mock.html` and drops the query string.
- Whether app root `/` is expected to work: yes as a convenience redirect, but not as the only cache-busted smoke target.
- Whether `/ui/steel-guitar-rag-mock.html` works: yes.
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes.
- Who should test this URL: the user and Lane 12.
- Do not test these URLs: do not treat local `127.0.0.1` or unauthenticated API fallback as protected-preview browser smoke.
- Known caveats: root drops the query string; use direct `/ui/...?...` URLs for exact smoke.

## Exact URLs tested

- Main app: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=fd342b9`
- Explorer: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=fd342b9`
- Root: `https://app.steelguitarrag.com/?v=fd342b9`

Root behavior:

- Root redirected to `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`.
- Query string was dropped.
- Use the direct cache-busted main app URL above for exact smoke.

## Header button visual result

| Check | Status | Evidence |
|---|---|---|
| Cloudflare Access login | Pass | Main app loaded without Cloudflare login page. |
| Q&A unlocks / input visible | Pass | `#question` textarea present. |
| Explore Fretboard visible upper-right | Pass | Link text `Explore Fretboard`; class `header-action-button explorer-header-link`. |
| Backstage/settings action visible separately | Pass | Button text `Go Backstage`; class `header-action-button backstage-trigger`; `aria-controls="backstage"`. |
| Explore Fretboard destination preserved | Pass | `href="/ui/e9-fretboard-explorer.html"`. |
| Explore Fretboard opens Explorer | Pass | Click opened `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html`. |
| Shared style family | Pass | Both controls use `header-action-button`. |
| Same normal UI font family | Pass | Both use `"Gill Sans", "Gill Sans MT", "Avenir Next", "Segoe UI", system-ui, -apple-system, sans-serif`. |
| Decorative/display font absent | Pass | No decorative/display font inherited by Explore Fretboard. |
| Same font size/weight | Pass | Both `14px`, weight `800`. |
| Same padding | Pass | Both `0px 16px`. |
| Same border/radius | Pass | Both `1px solid rgba(240, 191, 105, 0.34)`, radius `999px`. |
| Same height/top alignment | Pass | Both height `42px`, top `16px`. |
| Same icon treatment | Pass | Both controls include one SVG icon. |
| Removed vague chip `Explain this lick like a steel player would` absent | Pass | Not present. |
| Removed vague chip `Show me a smoother turnaround` absent | Pass | Not present. |
| Relevant console errors | Pass | No main-app console errors captured. |

Computed style evidence:

```text
Explore Fretboard:
font-family "Gill Sans", "Gill Sans MT", "Avenir Next", "Segoe UI", system-ui, -apple-system, sans-serif
font-size 14px
font-weight 800
padding 0px 16px
border 1px solid rgba(240, 191, 105, 0.34)
border-radius 999px
height 42px
top 16px
svg count 1

Go Backstage:
font-family "Gill Sans", "Gill Sans MT", "Avenir Next", "Segoe UI", system-ui, -apple-system, sans-serif
font-size 14px
font-weight 800
padding 0px 16px
border 1px solid rgba(240, 191, 105, 0.34)
border-radius 999px
height 42px
top 16px
svg count 1
```

## Explorer result

| Check | Status | Evidence |
|---|---|---|
| Explorer loads through Cloudflare Access | Pass | `E9 Fretboard Explorer - Steel Guitar RAG`. |
| 12 combined key choices | Pass | Key selector shows 12 entries: C, C#/Db, D, D#/Eb, E, F, F#/Gb, G, G#/Ab, A, A#/Bb, B. |
| No duplicate accidental key list | Pass | Enharmonics are combined in a single selector option. |
| No standalone disabled/greyed 5&8 branch option in Harmony/View | Pass | Harmony/View selector has only `2-string harmonized scale` and `3-string diatonic harmony`. |
| Bad internal deterministic/source-card copy absent | Pass | The bad copy string was not present. |
| No raw `five_eight_branch` label | Pass | Not visible. |
| No `[object Object]` | Pass | Not visible. |
| Relevant console errors | Pass | No Explorer console errors captured. |

## Prompt spot-check results

| Prompt | Status | Evidence |
|---|---|---|
| `Show me an A-flat major string grouping.` | Pass | Fretboard-first, no generic fallback, no tab block, no source cards. |
| `Show me a G harmonized scale.` | Pass | Static fretboard-first answer, no tab block, no source cards. |
| `Show me a G harmonized scale on strings 5 and 8.` | Pass | Static 5&8 branch answer, no tab block, no source cards. |
| `Show me a G major grip.` | Pass | Static grip answer is fretboard-first, no rendered tab/code block, no `tab_example` wording. |
| `Show me a G to C move.` | Pass | Movement answer rendered deterministic tab plus matching fretboard. |
| `Give me the full tab for a modern copyrighted song.` | Pass | Refused safely, no source cards, no tab, no fretboard. |
| `What are good Fender Steel King settings?` | Pass | Gear answer rendered normally with source cards and no stale tab/fretboard payload. |

Shared spot-check results:

- No `[object Object]`.
- No generic fallback.
- Static grip/position answers remain fretboard-first and do not show `tab_example` by default.
- Movement prompt may include deterministic tab.
- Copyright prompt refuses/redirects safely.
- Gear prompt has no stale tab/fretboard payload.

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
```

Browser checks:

- Main app URL loaded through Cloudflare Access.
- Root URL redirect checked.
- Header button computed style inspected.
- Explorer header link clicked.
- Explorer direct URL loaded.
- Prompt spot checks submitted through UI.

Skipped / caveated:

- `deploy/macos/install-private-preview-launchdaemon.sh status` and `version` required sudo and failed in non-interactive shell.

## Files changed

- Created `docs/handoffs/task-completions/2026-06-23-12-fretboard-button-style-protected-smoke.md`.

No implementation files were changed.

## Risks

Risk: low.

Reasons:

- Runtime is current at `fd342b9`.
- Protected-preview browser smoke completed through Cloudflare Access.
- Header style fix passed with computed style evidence.
- Explorer and focused prompt spot checks passed.
- Remaining warning is the known root query-string drop plus sudo-only helper status scripts.

## Blockers

No Lane 12 runtime/deployment blocker remains.

Potential follow-up:

- Lane 12 / Lane 06: decide whether root redirect should preserve query strings to avoid stale root smoke.

## Human decision needed

No.

## Safe-to-stage files

- `docs/handoffs/task-completions/2026-06-23-12-fretboard-button-style-protected-smoke.md`

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
Lane 01: Refresh integration-status.md after Lane 12 completed fretboard header button style protected-preview smoke at runtime fd342b9. Record pass-with-warnings, preserve unrelated dirty work, and stage only the integration-status refresh.
```

## Commit readiness

Safe to commit as a docs-only protected-preview smoke handoff.
