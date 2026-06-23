# Integration Status - Current Reset Snapshot

Generated for ChatGPT reset/guidance on branch `feature/answer-api`.

## Current State

- Current branch: `feature/answer-api`.
- Current repo HEAD at this refresh: `94fc745 docs: record explorer rendering filter protected smoke`.
- Latest protected-preview smoke docs commit: `94fc745`.
- Runtime smoked: `283468b`.
- Protected-preview status: **PASS**.
- User-smoke status: **allowed**.
- App control state: **can be parked with known caveats**.
- Broad unrelated dirty/untracked work remains parked. Do not broad-stage.

## Runtime / Deployment

- Cloudflare Access login: succeeded.
- Runtime refreshed from stale `f2581f8` to committed runtime `283468b`.
- `/api/version` reports `283468b`.
- Main app loaded through protected preview.
- Explorer loaded through protected preview.
- Explorer rendering/filter state passed.
- Main app spot check passed.
- Prompt matrix spot checks passed.
- Brand/app routing remains usable through direct protected-preview UI paths.
- No backend, UI, deployment, auth, DNS, corpus, Chroma/vector store, embeddings, scraping, private-source, source-inbox, or paid transcript files were changed by this refresh.

Latest runtime identity from Lane 12:

```text
git_sha=283468b
git_branch=feature/answer-api
auth_provider=cloudflare_access
retrieval_mode=hybrid_private_first
```

## Latest Protected-Preview Smoke

Latest Lane 12 handoff:

- `docs/handoffs/task-completions/2026-06-23-12-explorer-rendering-filter-protected-smoke.md`
- Handoff/docs commit: `94fc745 docs: record explorer rendering filter protected smoke`
- Runtime smoked: `283468b`
- Result: **PASS**
- API fallback: not used as browser-smoke proof

Smoke URLs:

```text
Explorer:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=283468b

Main app:
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=283468b

Root:
https://app.steelguitarrag.com/?v=283468b
```

Root caveat:

- `https://app.steelguitarrag.com/?v=283468b` redirects to `/ui/steel-guitar-rag-mock.html`.
- The root redirect drops the query string.
- Use direct cache-busted `/ui/...?...` URLs when exact cache-busting matters.

## Explorer Rendering / Filter Result

Lane 12 verified the protected-preview Explorer state at runtime `283468b`:

- G major, `3-string diatonic harmony`, all groups: `34` cards / `34` SVG highlights.
- G major, `2-string groups`, all groups: `44` cards / `44` SVG highlights.
- G major, `2-string groups`, `5-8`: `4` cards / `4` SVG highlights.
- Returning to `3-string diatonic harmony` reset group selection to all and rendered `34` cards / `34` SVG highlights.
- `5-8` appears under `2-string groups`, not as a standalone `5&8` Harmony/View option.
- No visible raw `five_eight_branch`.
- No `[object Object]`.
- No browser console errors.

Main app spot checks also passed through the protected-preview UI:

- `Show me a G major grip.`
- `Show me a G to C move.`
- `Give me the full tab for a modern copyrighted song.`

Known observation:

- Source-free responses still show the empty `Source notes / No sources returned` section. Lane 12 did not classify this as a populated source-card leak.

## Caveat Routing

- Root cache-bust redirect behavior: Lane 12 Self-Hosted Deployment.
- Empty source-note section for source-free answers, if product wants it hidden: Lane 06 UX/UI Design.

## Current Git / Worktree Notes

Current checked state at this refresh:

- Branch: `feature/answer-api`.
- Repo HEAD before this docs refresh: `94fc745`.
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
- `docs/handoffs/task-completions/2026-06-23-01-explorer-rendering-filter-integration-refresh.md`

## Files Not To Stage For This Refresh

- Backend/runtime files, tests, UI files, deployment/launchd files, auth/DNS/Cloudflare config, tunnel files, source files, paid transcript files, or app assets.
- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, generated corpus outputs, scraper output, source-inbox raw/provenance files.
- Deployment secrets, private env files, rendered plists, tunnel tokens, tunnel credentials, `.wrangler/`, and any secrets.
- `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, generated visual assets, and unrelated UI/assets.
- Unrelated handoffs or generated reports.

## Recommended Control State

Park the app with known caveats.

Use these exact URLs after Cloudflare Access login:

```text
Explorer:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=283468b

Main app:
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=283468b
```

For cache-busted validation, prefer direct `/ui/...?...` URLs because root redirects to `/ui/steel-guitar-rag-mock.html` and drops query strings.
