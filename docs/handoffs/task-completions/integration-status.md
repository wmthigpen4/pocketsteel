# Integration Status - Current Reset Snapshot

Generated for ChatGPT reset/guidance on branch `feature/answer-api`.

## Current State

- Current branch: `feature/answer-api`.
- Current repo HEAD at this refresh: `efc3660 docs: record explorer visual grip protected smoke`.
- Latest protected-preview smoke docs commit: `efc3660`.
- Runtime smoked: `1d3728a`.
- Protected-preview status: **PASS**.
- User-smoke status: **allowed**.
- App control state: **can be parked after user smoke with known caveats**.
- Broad unrelated dirty/untracked work remains parked. Do not broad-stage.

## Runtime / Deployment

- Cloudflare Access login: succeeded.
- Runtime refreshed from stale `17f2b55` to committed runtime `1d3728a`.
- `/api/version` reports `1d3728a`.
- Main app loaded through protected preview.
- Explorer loaded through protected preview.
- Explorer visual grip rendering passed.
- Answer-page G chord fretboard kept standard styling and did not inherit Explorer prominent mode.
- No backend, UI, deployment, auth, DNS, corpus, Chroma/vector store, embeddings, scraping, private-source, source-inbox, or paid transcript files were changed by this refresh.

Latest runtime identity from Lane 12:

```text
git_sha=1d3728a
git_branch=feature/answer-api
auth_provider=cloudflare_access
retrieval_mode=hybrid_private_first
```

## Latest Protected-Preview Smoke

Latest Lane 12 handoff:

- `docs/handoffs/task-completions/2026-06-23-12-explorer-visual-grip-rendering-protected-smoke.md`
- Handoff/docs commit: `efc3660 docs: record explorer visual grip protected smoke`
- Runtime smoked: `1d3728a`
- Result: **PASS**
- API fallback: not used as browser-smoke proof

Smoke URLs:

```text
Explorer:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=1d3728a

Main app:
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=1d3728a

Root:
https://app.steelguitarrag.com/?v=1d3728a
```

Root caveat:

- `https://app.steelguitarrag.com/?v=1d3728a` redirects to `/ui/steel-guitar-rag-mock.html`.
- The root redirect drops the query string.
- Use direct cache-busted `/ui/...?...` URLs when exact cache-busting matters.

## Explorer Visual Grip Rendering Result

Lane 12 verified the protected-preview Explorer state at runtime `1d3728a`:

- Explorer loaded refreshed `visual-grip-render-20260623` script cache-busts.
- Selected Explorer groups visibly render localized fret/string clusters.
- Full-string horizontal lanes are absent.
- SVG clusters match selected cards/rows.
- No visible raw `five_eight_branch`.
- No `[object Object]`.
- No relevant browser console errors.

Selected states verified:

| State | Cards | Highlights | Dots | Dot strings | Full-string lane suspect | Result |
| --- | ---: | ---: | ---: | --- | --- | --- |
| G major / 3-string / `3-4-5` | 8 | 8 | 24 | `3,4,5` | false | Pass |
| G major / 3-string / `5-6-8` | 5 | 5 | 15 | `5,6,8` | false | Pass |
| G major / 3-string / `6-8-10` | 5 | 5 | 15 | `6,8,10` | false | Pass |
| A major / 3-string / `6-8-10` | 5 | 5 | 15 | `6,8,10` | false | Pass |
| G major / 2-string / `5-8` | 4 | 4 | 8 | `5,8` | false | Pass |

Main app comparison:

- Prompt: `How do I play a G chord?`
- Answer rendered.
- Fretboard visible.
- Answer-page G chord fretboard stayed standard localized styling.
- Explorer-only prominent cluster styling did not leak into the answer-page fretboard.
- No tab card, no fallback text, and no `[object Object]`.

## Caveat Routing

- Root cache-bust redirect behavior: Lane 12 Self-Hosted Deployment.
- `deploy/macos/install-private-preview-launchdaemon.sh status` still needs interactive sudo in this environment. Runtime health was verified through `launchctl print`, `lsof`, `ps`, and `/api/version`.

## Current Git / Worktree Notes

Current checked state at this refresh:

- Branch: `feature/answer-api`.
- Repo HEAD before this docs refresh: `efc3660`.
- Cached index before this docs refresh: empty.
- `git diff --check`: to be run for this docs refresh.

Broad parked dirty/untracked work remains outside this refresh, including:

- README/docs/provenance/legal/source-policy edits.
- Corpus metadata and source-inbox metadata.
- Root RAG/corpus helper scripts.
- Private/corpus-adjacent scripts and data.
- Landing/sign/brand assets and generated visual files.
- Historical untracked handoffs and screenshot/report assets.

Do not stage parked work unless a later exact-scope handoff approves it.

## Blockers

No hard protected-preview blocker is known from the latest Lane 12 smoke.

This is a protected-preview **PASS** with the root cache-bust caveat preserved.

## Safe To Stage For This Refresh

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-23-01-explorer-visual-grip-integration-refresh.md`

## Files Not To Stage For This Refresh

- Backend/runtime files, tests, UI files, deployment/launchd files, auth/DNS/Cloudflare config, tunnel files, source files, paid transcript files, or app assets.
- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, generated corpus outputs, scraper output, source-inbox raw/provenance files.
- Deployment secrets, private env files, rendered plists, tunnel tokens, tunnel credentials, `.wrangler/`, and any secrets.
- `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, generated visual assets, and unrelated UI/assets.
- Unrelated handoffs or generated reports.

## Recommended Control State

Park the app after user smoke with known caveats.

Use these exact URLs after Cloudflare Access login:

```text
Explorer:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=1d3728a

Main app:
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=1d3728a
```

For cache-busted validation, prefer direct `/ui/...?...` URLs because root redirects to `/ui/steel-guitar-rag-mock.html` and drops query strings.
