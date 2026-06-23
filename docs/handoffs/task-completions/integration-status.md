# Integration Status - Current Reset Snapshot

Generated for ChatGPT reset/guidance on branch `feature/answer-api`.

## Current State

- Current branch: `feature/answer-api`.
- Current repo HEAD at this refresh: `7db94f7 docs: record restored header font protected smoke`.
- Latest protected-preview smoke docs commit: `7db94f7`.
- Runtime smoked: `706d8cd`.
- Protected-preview status: **pass with product caveat**.
- User-smoke status: **allowed; evaluate the restored header font behavior in user smoke**.
- App control state: **can be parked if the restored inherited header font is acceptable**.
- Broad unrelated dirty/untracked work remains parked. Do not broad-stage.

## Runtime / Deployment

- Cloudflare Access login: succeeded.
- LaunchDaemon runtime refreshed from stale `b547178` to `706d8cd`.
- `/api/version` reports `706d8cd`.
- Main app loaded through protected preview.
- Explorer loaded through protected preview.
- Header buttons use the restored accepted inherited typography behavior.
- Rejected explicit neutral stack from `b547178` is gone.
- Explorer checks passed.
- Prompt spot checks passed.
- LaunchDaemon owns the app runtime.
- Manual screen runtime is absent.
- Cloudflare Tunnel is running.
- No backend, UI, deployment, auth, DNS, corpus, Chroma/vector store, embeddings, scraping, private-source, source-inbox, or paid transcript files were changed by this refresh.

Latest runtime identity from Lane 12:

```text
git_sha=706d8cd
git_branch=feature/answer-api
auth_provider=cloudflare_access
retrieval_mode=hybrid_private_first
```

## Latest Protected-Preview Smoke

Latest Lane 12 handoff:

- `docs/handoffs/task-completions/2026-06-23-12-restored-header-font-protected-smoke.md`
- Handoff commit: `7db94f7 docs: record restored header font protected smoke`
- Runtime smoked: `706d8cd`
- Result: **pass with product caveat**
- API fallback: not used as browser-smoke proof

Smoke URLs:

```text
Main app:
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=706d8cd

E9 Fretboard Explorer:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=706d8cd

Root:
https://app.steelguitarrag.com/?v=706d8cd
```

Root caveat:

- `https://app.steelguitarrag.com/?v=706d8cd` redirects to `/ui/steel-guitar-rag-mock.html`.
- The root redirect drops the query string.
- Use direct cache-busted `/ui/...?...` URLs when exact cache-busting matters.

## Restored Header Font Smoke Result

Passed:

- Cloudflare Access protected-preview login.
- Main app shell and Q&A surface.
- Root redirect behavior observed.
- Header button restored font behavior:
  - `Explore Fretboard` and `Go Backstage` use the restored inherited app-page typography behavior.
  - Both controls inherit the app font stack beginning with `Gill Sans`.
  - The rejected explicit neutral system stack from `b547178` is no longer present.
  - `Explore Fretboard` remains visible in the upper-right header area and links to `/ui/e9-fretboard-explorer.html`.
  - `Go Backstage` remains a separate header action and opens/toggles Backstage/settings.
- Explorer checks:
  - Explorer loaded through Cloudflare Access.
  - 12 combined key choices present.
  - No duplicate accidental key list.
  - No standalone 5&8 branch option in Harmony/View.
  - Bad internal deterministic/source-card copy absent.
  - No relevant browser console errors.
- Prompt spot checks:
  - `Show me a G major grip.` passed.
  - `Show me a G to C move.` passed.
  - `Give me the full tab for a modern copyrighted song.` passed.

Product caveat:

- Restored behavior inherits the app font stack beginning with `Gill Sans`.
- This is intentional for this slice and matches the requested prior accepted mechanism from git history.
- If user smoke rejects it, next step is a product decision on the exact explicit button font before another Lane 06 pass.

Known caveats preserved:

1. Root URL redirects to `/ui/steel-guitar-rag-mock.html` and drops the query string.
2. Restored header font inherits the Gill Sans-backed app stack.
3. Exact explicit button font remains a product decision only if user smoke rejects this restored behavior.

## Caveat Routing

- Root cache-bust behavior: Lane 12 Self-Hosted Deployment.
- Header button exact explicit font decision, if restored behavior is rejected: Product decision first, then Lane 06 UX/UI Design.

## Current Git / Worktree Notes

Current checked state at this refresh:

- Branch: `feature/answer-api`.
- Repo HEAD: `7db94f7`.
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

This is not a clean pass because the restored inherited header font remains a product caveat for user smoke.

## Safe To Stage For This Refresh

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-23-01-restored-header-font-integration-refresh.md`

## Files Not To Stage For This Refresh

- Backend/runtime files, tests, UI files, deployment/launchd files, auth/DNS/Cloudflare config, tunnel files, source files, paid transcript files, or app assets.
- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, generated corpus outputs, scraper output, source-inbox raw/provenance files.
- Deployment secrets, private env files, rendered plists, tunnel tokens, tunnel credentials, `.wrangler/`, and any secrets.
- `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, generated visual assets, and unrelated UI/assets.
- Unrelated handoffs or generated reports.

## Recommended Control State

Park the app if the restored inherited header font is acceptable in user smoke.

Use these exact URLs after Cloudflare Access login:

```text
Main app:
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=706d8cd

E9 Fretboard Explorer:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=706d8cd
```

Route follow-up work by lane:

- Lane 12 for root cache-bust/redirect behavior.
- Product decision first, then Lane 06, if the exact explicit header button font needs to change.
