# Integration Status - Current Reset Snapshot

Generated for ChatGPT reset/guidance on branch `feature/answer-api`.

## Current State

- Current branch: `feature/answer-api`.
- Current repo HEAD at this refresh: `760dc73 docs: record explorer UI cleanup protected smoke`.
- Latest protected-preview smoke docs commit: `760dc73`.
- Runtime smoked: `e1103be`.
- Protected-preview status: **pass with warnings**.
- User-smoke status: **allowed if the warnings below are acceptable; this is not a clean pass**.
- Broad unrelated dirty/untracked work remains parked. Do not broad-stage.

## Runtime / Deployment

- Cloudflare Access login: succeeded.
- Main app loaded through protected preview.
- Explorer loaded through protected preview.
- Main UI, Explorer cleanup, prompt matrix, and brand asset routing passed.
- LaunchDaemon owns the app runtime.
- Manual screen runtime is absent.
- Cloudflare Tunnel is running.
- No backend, UI, deployment, auth, DNS, corpus, Chroma/vector store, embeddings, scraping, private-source, source-inbox, or paid transcript files were changed by this refresh.

Latest runtime identity from Lane 12:

```text
git_sha=e1103be
git_branch=feature/answer-api
auth_provider=cloudflare_access
retrieval_mode=hybrid_private_first
```

Browser direct `/api/version` caveat:

- Browser direct navigation to `https://app.steelguitarrag.com/api/version` was blocked by the browser client with `net::ERR_BLOCKED_BY_CLIENT`.
- Local `/api/version` confirmed runtime `e1103be`.
- Route to Lane 12 only if browser-visible version diagnostics are required.

## Latest Protected-Preview Smoke

Latest Lane 12 handoff:

- `docs/handoffs/task-completions/2026-06-23-12-explorer-ui-cleanup-protected-smoke.md`
- Handoff commit: `760dc73 docs: record explorer UI cleanup protected smoke`
- Runtime smoked: `e1103be`
- Result: **pass with warnings**
- API fallback: not used as browser-smoke proof

Smoke URLs:

```text
Main app:
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=e1103be

E9 Fretboard Explorer:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e1103be

Root:
https://app.steelguitarrag.com/?v=e1103be

Brand SVG asset:
https://app.steelguitarrag.com/brand/pedal-steel-fretboard-background.svg?v=e1103be
```

Root caveat:

- `https://app.steelguitarrag.com/?v=e1103be` redirects to `/ui/steel-guitar-rag-mock.html`.
- The root redirect drops the query string.
- Use direct cache-busted `/ui/...?...` URLs when exact cache-busting matters.

## Explorer Cleanup Smoke Result

Passed:

- Cloudflare Access protected-preview login.
- Main app shell and Q&A surface.
- Explorer route and Explorer click-through.
- Explorer cleanup: 12 combined key choices, no duplicate enharmonic key entries, no standalone `five_eight_branch` view option, 5-8 remains available in the correct context, and no raw `five_eight_branch` label.
- Prompt matrix.
- Brand asset routing, including the protected SVG asset route.
- No API fallback was used as browser-smoke proof.

Warnings preserved:

1. Root URL drops cache-bust on redirect.
2. Backstage button is functional but visible text is `Get a Backstage Pass`, not `Go Backstage`.
3. Browser direct `/api/version` navigation was blocked by browser client; local `/api/version` confirmed runtime.
4. Explorer console warning after select/asset smoke: `Cannot use 'in' operator to search for 'animation' in undefined`.
5. Prior warning still visible until closed: `tab_example_event` / `Tab event` wording on static grip.
6. Prior warning still visible until closed: Ab/A-flat fretboard labels canonicalize as `G# major`.

## Warning Routing

- Root cache-bust behavior: Lane 12 Self-Hosted Deployment.
- Backstage visible label change, if desired: Lane 06 UX/UI Design.
- Browser-visible `/api/version` diagnostics, if required: Lane 12 Self-Hosted Deployment.
- Explorer console warning: Lane 06 UX/UI Design.
- `tab_example_event` / `Tab event` wording: Lane 05 if the API payload/detail contract owns the wording; Lane 06 if this is only display-label handling.
- Ab/A-flat canonicalization to `G# major` fretboard labels: Lane 05 Backend / RAG Integration.

## Current Git / Worktree Notes

Current checked state at this refresh:

- Branch: `feature/answer-api`.
- Repo HEAD: `760dc73`.
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

This is not a clean pass because the warnings above remain.

## Safe To Stage For This Refresh

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-23-01-explorer-cleanup-integration-refresh.md`

## Files Not To Stage For This Refresh

- Backend/runtime files, tests, UI files, deployment/launchd files, auth/DNS/Cloudflare config, tunnel files, source files, paid transcript files, or app assets.
- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, generated corpus outputs, scraper output, source-inbox raw/provenance files.
- Deployment secrets, private env files, rendered plists, tunnel tokens, tunnel credentials, `.wrangler/`, and any secrets.
- `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, generated visual assets, and unrelated UI/assets.
- Unrelated handoffs or generated reports.

## Recommended Control State

Park the app with known warnings, or choose a follow-up warning slice.

Use these exact URLs after Cloudflare Access login if user smoke continues:

```text
Main app:
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=e1103be

E9 Fretboard Explorer:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e1103be
```

Route follow-up work by lane:

- Lane 12 for root cache-bust/redirect behavior or browser-visible version diagnostics.
- Lane 05 for API payload/detail contract wording and Ab/A-flat backend canonicalization.
- Lane 06 for Backstage label preference, Explorer console warning, or display-label-only cleanup if payloads are already correct.
- Lane 15 for regression matrix or smoke QA.
