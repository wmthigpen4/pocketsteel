# Integration Status - Current Reset Snapshot

Generated for ChatGPT reset/guidance on branch `feature/answer-api`.

## Current State

- Current branch: `feature/answer-api`.
- Current repo HEAD at this refresh: `2728154 docs: record post-restart harmonized scale smoke`.
- Current protected-preview runtime `/api/version`: `ddd7953`.
- Protected-preview status: **usable / passed**.
- User-smoke status: **ready to use; park the app for the day unless a new real blocker appears**.
- Broad unrelated dirty/untracked work remains parked. Do not broad-stage.

## Runtime / Deployment

- LaunchDaemon supervision: active.
- App LaunchDaemon: `system/com.steelguitarrag.private-preview` running.
- Python listener: PID `72903` on `127.0.0.1:8770`.
- Runtime start time: Tue Jun 23 13:18:17 2026.
- Runtime `/api/version`: `git_sha=ddd7953`, `git_branch=feature/answer-api`, `auth_provider=cloudflare_access`, `retrieval_mode=hybrid_private_first`.
- Manual screen runtime: absent.
- Cloudflare Tunnel: running.
- No DNS, Cloudflare Access policy, auth, secrets, deployment config, corpus, Chroma/vector store, embeddings, scraping, or private-source data changed in the latest verification work.

## Latest Protected-Preview Smoke

Latest successful Lane 12 smoke handoff:

- `docs/handoffs/task-completions/2026-06-23-12-post-restart-harmonized-scale-smoke.md`
- Follow-up handoff commit: `2728154 docs: record post-restart harmonized scale smoke`.
- Runtime smoked: `ddd7953`.
- Cloudflare Access login: succeeded.
- Main app smoke: passed.
- Explorer smoke: passed.
- Root check: passed with caveat.

Smoke target:

```text
Main app:
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=ddd7953

E9 Fretboard Explorer:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=ddd7953
```

Root caveat:

- `https://app.steelguitarrag.com/?v=ddd7953` redirects to `/ui/steel-guitar-rag-mock.html`.
- The root redirect drops the query string.
- Use direct cache-busted `/ui/...?...` URLs when exact cache-busting matters.

## Harmonized-Scale Feature Status

Broader G harmonized-scale routing is complete, committed, restarted, and protected-preview smoked.

Passed prompt families:

- Broader G major harmonized-scale prompts.
- G natural minor harmonized-scale prompts.
- F# diminished position in G.
- A diminished position in G minor.
- G harmonized scale on strings 5 and 8.
- Static grip, movement/tab, copyright, and gear regressions.
- Explorer 5&8 UI route and label behavior.

Current behavior:

- Broader G major prompts no longer show generic fallback.
- G natural minor prompts no longer show generic fallback.
- F# diminished and A diminished prompts no longer show generic fallback.
- Static harmonized-scale answers are fretboard-first, source-free, warning-free, and `tab_example`-free by default.
- Existing G 5&8 branch correction remains intact.
- Explorer 5&8 UI passes and does not expose raw internal branch labels.

Relevant committed work:

- `239f74a fix: route G harmonized scale prompts deterministically`
- `7da25e8 fix: route harmonized scale prompts through answer API`
- `db6ae81 fix: route browser harmonized scale prompts deterministically`
- `0ad025f fix: prevent harmonized scale fallback display`
- `ddd7953 docs: record displayed harmonized scale protected smoke`
- `2728154 docs: record post-restart harmonized scale smoke`

## Current Git / Worktree Notes

Current checked state at this refresh:

- Branch: `feature/answer-api`.
- Repo HEAD: `2728154`.
- Cached index before this docs refresh: empty.
- `git diff --check`: passed before this docs refresh.

Broad parked dirty/untracked work remains outside this refresh, including:

- README/docs/provenance/legal/source-policy edits.
- Corpus metadata and source-inbox metadata.
- Root RAG/corpus helper scripts.
- Private/corpus-adjacent scripts and data.
- Landing/sign/brand assets and generated visual files.
- Historical untracked handoffs and screenshot/report assets.

Do not stage parked work unless a later exact-scope handoff approves it.

## Blockers

No known protected-preview blockers remain for today's state.

## Safe To Stage For This Refresh

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-23-01-final-harmonized-scale-integration-refresh.md`

## Files Not To Stage For This Refresh

- Backend/runtime files, tests, UI files, deployment/launchd files, auth/DNS/Cloudflare config, tunnel files, source files, or app assets.
- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, generated corpus outputs, scraper output, source-inbox raw/provenance files.
- Deployment secrets, private env files, rendered plists, tunnel tokens, tunnel credentials, `.wrangler/`, and any secrets.
- `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, generated visual assets, and unrelated UI/assets.
- Unrelated handoffs or generated reports.

## Recommended Control State

Park the app for the day.

Use these exact URLs after Cloudflare Access login if user smoke continues:

```text
Main app:
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=ddd7953

E9 Fretboard Explorer:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=ddd7953
```

Route any new defects by lane:

- Lane 05 Backend / RAG Integration for answer routing, deterministic-answer, source-card, or API behavior issues.
- Lane 06 UX/UI Design for UI, fretboard, tab, Explorer, or rendering issues.
- Lane 11 Auth / Security for Cloudflare Access/auth/session issues.
- Lane 12 Self-Hosted Deployment for runtime, version, restart, log, tunnel, or deployment issues.
- Lane 15 QA / Answer Eval for regression matrix, smoke, or verification tasks.
