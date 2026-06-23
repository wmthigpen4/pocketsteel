# Integration Status - Current Reset Snapshot

Generated for ChatGPT reset/guidance on branch `feature/answer-api`.

## Current State

- Current branch: `feature/answer-api`.
- Current repo HEAD at this refresh: `08221a6 docs: complete smoke feedback protected preview`.
- Latest protected-preview smoke commit: `08221a6`.
- Current protected-preview runtime `/api/version`: `1c0bbd6`.
- Protected-preview status: **pass with warnings**.
- User-smoke status: **allowed if the warnings below are acceptable; this is not a clean pass**.
- Broad unrelated dirty/untracked work remains parked. Do not broad-stage.

## Runtime / Deployment

- Cloudflare Access login: succeeded.
- Main app loaded through protected preview.
- Explorer loaded through protected preview.
- Prompt matrix passed except documented UX warnings.
- LaunchDaemon owns the app runtime.
- Manual screen runtime is absent.
- Cloudflare Tunnel is running.
- No backend, UI, deployment, auth, DNS, corpus, Chroma/vector store, embeddings, scraping, private-source, source-inbox, or paid transcript files were changed by this refresh.

Latest runtime identity from Lane 12:

```text
git_sha=1c0bbd6
git_branch=feature/answer-api
auth_provider=cloudflare_access
retrieval_mode=hybrid_private_first
```

## Latest Protected-Preview Smoke

Latest Lane 12 handoff:

- `docs/handoffs/task-completions/2026-06-23-12-smoke-feedback-protected-preview-final.md`
- Handoff commit: `08221a6 docs: complete smoke feedback protected preview`
- Runtime smoked: `1c0bbd6`
- Result: **pass with warnings**
- API fallback: not used as browser-smoke proof

Smoke URLs:

```text
Main app:
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=1c0bbd6

E9 Fretboard Explorer:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=1c0bbd6
```

Root caveat:

- `https://app.steelguitarrag.com/?v=1c0bbd6` redirects to `/ui/steel-guitar-rag-mock.html`.
- The root redirect drops the query string.
- The redirected root surface may show stale prompt-chip copy.
- Use direct cache-busted `/ui/...?...` URLs for exact smoke.

## Smoke Feedback Result

Passed:

- Cloudflare Access protected-preview login.
- Main app shell and Q&A surface.
- Explorer route and Explorer click-through.
- Prompt matrix, except for warnings listed below.
- Broader G harmonized-scale prompts.
- G natural minor harmonized-scale prompts.
- F# diminished and A diminished prompts.
- G 5&8 branch prompt.
- Static grip, movement/tab, copyright, and gear regressions.
- Explorer 5&8 branch UI and all-key selector behavior.

Warnings preserved:

1. Root URL drops cache-bust and may show stale prompt chips.
2. `Show me a G major grip.` exposes `tab_example_event` / `Tab event` wording in fretboard detail.
3. Ab/A-flat prose normalizes correctly, but fretboard card labels canonicalize the enharmonic chord as `G# major`.

## Warning Routing

- Root cache-bust behavior: Lane 12 Self-Hosted Deployment.
- `tab_example_event` / `Tab event` wording: Lane 05 if the API payload/detail contract owns the wording; Lane 06 if this is only display-label handling.
- Ab/A-flat canonicalization to `G# major` fretboard labels: Lane 05 Backend / RAG Integration.

## Current Git / Worktree Notes

Current checked state at this refresh:

- Branch: `feature/answer-api`.
- Repo HEAD: `08221a6`.
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

This is not a clean pass because the three warnings above remain.

## Safe To Stage For This Refresh

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-23-01-smoke-feedback-integration-refresh.md`

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
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=1c0bbd6

E9 Fretboard Explorer:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=1c0bbd6
```

Route follow-up work by lane:

- Lane 12 for root cache-bust/redirect behavior.
- Lane 05 for API payload/detail contract wording and Ab/A-flat backend canonicalization.
- Lane 06 for display-label-only cleanup if payloads are already correct.
- Lane 15 for regression matrix or smoke QA.
