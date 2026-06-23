# Integration Status - Current Reset Snapshot

Generated for ChatGPT reset/guidance on branch `feature/answer-api`.

## Current State

- Current branch: `feature/answer-api`.
- Current repo HEAD at this refresh: `78f6c14 docs: record fretboard button style protected smoke`.
- Latest protected-preview smoke docs commit: `78f6c14`.
- Runtime smoked: `fd342b9`.
- Protected-preview status: **pass with warnings**.
- User-smoke status: **allowed if the warnings below are acceptable; this is not a clean pass**.
- App control state: **can be parked with known warnings after user smoke**.
- Broad unrelated dirty/untracked work remains parked. Do not broad-stage.

## Runtime / Deployment

- Cloudflare Access login: succeeded.
- Main app loaded through protected preview.
- Explorer loaded through protected preview.
- Header button style fix passed.
- Explorer cleanup passed.
- Prompt spot checks passed.
- LaunchDaemon owns the app runtime.
- Manual screen runtime is absent.
- Cloudflare Tunnel is running.
- No backend, UI, deployment, auth, DNS, corpus, Chroma/vector store, embeddings, scraping, private-source, source-inbox, or paid transcript files were changed by this refresh.

Latest runtime identity from Lane 12:

```text
git_sha=fd342b9
git_branch=feature/answer-api
auth_provider=cloudflare_access
retrieval_mode=hybrid_private_first
```

LaunchDaemon helper caveat:

- `deploy/macos/install-private-preview-launchdaemon.sh status` and `version` required `sudo` in the Lane 12 shell and failed non-interactively.
- Lane 12 still supplied runtime evidence with `launchctl`, listener checks, and local `/api/version`.
- Route to Lane 12 only if this becomes operationally painful.

## Latest Protected-Preview Smoke

Latest Lane 12 handoff:

- `docs/handoffs/task-completions/2026-06-23-12-fretboard-button-style-protected-smoke.md`
- Handoff commit: `78f6c14 docs: record fretboard button style protected smoke`
- Runtime smoked: `fd342b9`
- Result: **pass with warnings**
- API fallback: not used as browser-smoke proof

Smoke URLs:

```text
Main app:
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=fd342b9

E9 Fretboard Explorer:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=fd342b9

Root:
https://app.steelguitarrag.com/?v=fd342b9
```

Root caveat:

- `https://app.steelguitarrag.com/?v=fd342b9` redirects to `/ui/steel-guitar-rag-mock.html`.
- The root redirect drops the query string.
- Use direct cache-busted `/ui/...?...` URLs when exact cache-busting matters.

## Fretboard Button Style Smoke Result

Passed:

- Cloudflare Access protected-preview login.
- Main app shell and Q&A surface.
- Header button visual fix:
  - `Explore Fretboard` visually matches `Go Backstage`.
  - Both controls use the shared `header-action-button` style family.
  - Both use the same UI font family, size, weight, padding, border, radius, height/top alignment, and SVG icon treatment.
  - Decorative/display font is gone from `Explore Fretboard`.
  - `Explore Fretboard` opens `/ui/e9-fretboard-explorer.html`.
  - `Go Backstage` remains separate and targets backstage/settings.
- Explorer cleanup:
  - 12 combined key choices present.
  - No duplicate accidental key list.
  - No standalone 5&8 branch option in Harmony/View.
  - Bad internal deterministic/source-card copy absent.
  - No relevant console errors.
- Prompt spot checks:
  - Static grip/position answers remain fretboard-first with no default tab.
  - Movement prompt can show deterministic tab.
  - Copyright prompt refuses safely.
  - Gear prompt has source cards and no stale tab/fretboard.

Warnings preserved:

1. Root URL drops cache-bust on redirect.
2. LaunchDaemon helper `status` and `version` commands require `sudo` in this shell, though `launchctl`, listener, and `/api/version` checks supplied runtime evidence.
3. Prior warning still visible until closed: `tab_example_event` / `Tab event` wording on static grip.
4. Prior warning still visible until closed: Ab/A-flat fretboard labels canonicalize as `G# major`.

## Warning Routing

- Root cache-bust behavior: Lane 12 Self-Hosted Deployment.
- LaunchDaemon helper sudo caveat: Lane 12 Self-Hosted Deployment only if it becomes operationally painful.
- `tab_example_event` / `Tab event` wording: Lane 05 if the API payload/detail contract owns the wording; Lane 06 if this is only display-label handling.
- Ab/A-flat canonicalization to `G# major` fretboard labels: Lane 05 Backend / RAG Integration.

## Current Git / Worktree Notes

Current checked state at this refresh:

- Branch: `feature/answer-api`.
- Repo HEAD: `78f6c14`.
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
- `docs/handoffs/task-completions/2026-06-23-01-fretboard-button-style-integration-refresh.md`

## Files Not To Stage For This Refresh

- Backend/runtime files, tests, UI files, deployment/launchd files, auth/DNS/Cloudflare config, tunnel files, source files, paid transcript files, or app assets.
- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, generated corpus outputs, scraper output, source-inbox raw/provenance files.
- Deployment secrets, private env files, rendered plists, tunnel tokens, tunnel credentials, `.wrangler/`, and any secrets.
- `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, generated visual assets, and unrelated UI/assets.
- Unrelated handoffs or generated reports.

## Recommended Control State

User smoke the header buttons, then park the app with known warnings.

Use these exact URLs after Cloudflare Access login:

```text
Main app:
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=fd342b9

E9 Fretboard Explorer:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=fd342b9
```

Route follow-up work by lane:

- Lane 12 for root cache-bust/redirect behavior or LaunchDaemon helper usability.
- Lane 05 for API payload/detail contract wording and Ab/A-flat backend canonicalization.
- Lane 06 for display-label-only cleanup if payloads are already correct.
- Lane 15 for regression matrix or smoke QA.
