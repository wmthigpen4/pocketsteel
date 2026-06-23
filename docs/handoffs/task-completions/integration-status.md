# Integration Status - Current Reset Snapshot

Generated for ChatGPT reset/guidance on branch `feature/answer-api`.

## Current Project State

- Current branch: `feature/answer-api`.
- Current repo HEAD at this refresh: `f15ef6c docs: record protected smoke after five eight label fix`.
- Current protected-preview runtime `/api/version`: `3a07c8f fix: hide five eight internal branch label`.
- Runtime branch from `/api/version`: `feature/answer-api`.
- Runtime retrieval mode from `/api/version`: `hybrid_private_first`.
- Runtime auth provider from `/api/version`: `cloudflare_access`.
- User-smoke readiness: **protected preview is ready for user smoke**.
- Broad unrelated dirty/untracked work remains parked. Do not broad-stage.

## Deployment / Runtime Status

LaunchDaemon supervision is active.

- App LaunchDaemon: loaded and running.
- LaunchDaemon program: `/usr/local/libexec/steel-guitar-rag/run-private-preview-app.sh`.
- LaunchDaemon working directory: `/usr/local/libexec/steel-guitar-rag`.
- App listener: launchd-owned Python process on `127.0.0.1:8770`.
- Manual screen runtime: removed; no screen sessions found in the latest Lane 12 smoke.
- Durable app logs:
  - stdout: `~/Library/Logs/steel-guitar-rag/app.out.log`
  - stderr: `~/Library/Logs/steel-guitar-rag/app.err.log`
- Log caveat: historical `Address already in use` stack traces remain in `app.err.log`, but current service is running and serving.
- Cloudflare Tunnel: running as the separate system LaunchDaemon `com.cloudflare.cloudflared`.
- No Cloudflare Access policy, DNS, tunnel token, auth setting, corpus, Chroma/vector store, embedding, scraping, or source-data changes were made by the latest smoke tasks.

## Latest Protected-Preview Smoke

Latest passing smoke handoff:

- `docs/handoffs/task-completions/2026-06-23-12-protected-smoke-after-five-eight-label-fix.md`

Pass/warn/fail:

- **Pass.**
- Launchd-supervised protected preview is running runtime commit `3a07c8f`.
- Main app protected-preview browser smoke passed.
- E9 Fretboard Explorer protected-preview browser smoke passed.
- Cloudflare Access login succeeded; product pages loaded, not the Access login page.
- Q&A unlocked and answered through the browser UI.

Smoke target block:

```text
Smoke Target:
- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=3a07c8f
- Cache-busted URL tested: https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=3a07c8f
- Exact URL the user should use:
  - Main app: https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=3a07c8f
  - Explorer: https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=3a07c8f
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: 3a07c8f
- Version endpoint: /api/version
- Version endpoint result: 3a07c8f on feature/answer-api
- Whether app root `/` works: yes, redirects to /ui/steel-guitar-rag-mock.html
- Whether app root `/` is expected to work: yes as a convenience redirect
- Whether /ui/steel-guitar-rag-mock.html works: yes
- Whether /ui/steel-guitar-rag-mock.html is expected to work: yes
- API fallback status: not used
- Known caveats: root redirect drops query strings; use direct /ui cache-busted URLs for exact smoke.
```

Main app smoke result:

- `Show me a G major grip.` - pass; fretboard visible; no tab block; no raw object string; no raw internal 5&8 label.
- `Show me a 4-5-6 grip.` - pass; fretboard visible; no tab block; no raw object string; no raw internal 5&8 label.
- `Where is G on E9?` - pass; teacher-first G position answer; fretboard visible.
- `Show me a G to C move.` - pass; direct answer, deterministic tab, matching fretboard.
- `How do I use A+B pedals?` - pass; direct answer, deterministic tab, matching fretboard.
- `Show me an E-lower move.` - pass; direct answer, deterministic tab, matching fretboard.
- `Give me a beginner lick in G.` - pass; direct prose, tab, and fretboard visible.
- `Show me a G harmonized scale on strings 5 and 8.` - pass; fretboard-first, source-free in the answer payload, warning-free, tab-free; visible text uses `5&8 branch`.
- Copyrighted song / whole-solo / YouTube transcription prompts - pass; clear refusals, no tab/fretboard.
- Gear prompts - pass; source-linked gear answers render without stale tab/fretboard payloads.
- Main app console/page errors: none captured.

Explorer smoke result:

- Explorer URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=3a07c8f`.
- Explorer route loads after Cloudflare Access login.
- G major is selectable and selected by default.
- `5&8 branch positions` appears as the human-facing harmony/view option.
- `5-8` appears as the string-group option.
- Four validated `5-8` rows render.
- Visible rows show friendly `5&8 branch`.
- Raw internal `five_eight_branch` visible text count: `0`.
- No raw object string.
- No Explorer console errors captured.

## G 5&8 Harmonized-Scale Status

Backend/API QA handoff:

- `docs/handoffs/task-completions/2026-06-23-15-g-harmonized-scale-qa.md`

Backend status:

- Commit `c08cc95 feat: add deterministic G harmonized scale rules` is in current branch history.
- Exact prompt `Show me a G harmonized scale on strings 5 and 8.` is deterministic, fretboard-first, source-free, warning-free, and tab-free.
- Validated G strings 5&8 branch rows:
  - fret 6, A pedal + E-raise/F lever, strings 5&8, notes G/B
  - fret 8, E-lower, strings 5&8, notes G/B
  - fret 11, A pedal + E-raise/F lever, strings 5&8, notes C/E
  - fret 13, E-lower, strings 5&8, notes C/E
- Corrected fret 13 E-lower C/E is present.
- Incorrect fret 11 E-lower C/E is absent.
- Diminished/partial voicing regression checks passed; partial diminished rows do not falsely claim full m7b5.

Explorer/UI status:

- Commit `0d10843 fix: label g five eight fretboard branch` exposed the `5&8 branch positions` UI and `5-8` filter.
- Commit `3a07c8f fix: hide five eight internal branch label` fixed the raw internal label leak.
- Latest protected-preview smoke confirms the UI fix is live in the protected preview.

Known adjacent non-blockers:

- Broader harmonized-scale prompts such as `Show me a G harmonized scale.` were previously called out by QA as adjacent Lane 05 follow-up candidates if product wants broader deterministic routing.
- That adjacent routing work is not a blocker for the current protected-preview user-smoke readiness because the scoped 5&8 prompt and Explorer UI passed.

## Current Git / Worktree Status

Current checked state from this refresh:

- Branch: `feature/answer-api`.
- Repo HEAD: `f15ef6c`.
- Cached index before this docs refresh: empty.
- `git diff --check`: passed before this docs refresh.

Dirty runtime-affecting files currently visible in the worktree:

- `pocketsteel/curated_answers.py`
- `pocketsteel/fretboard_examples.py`
- `tests/test_api_search.py`

Other broad parked dirty/untracked categories include:

- README/docs/provenance/legal/source-policy edits.
- Corpus metadata and source-inbox metadata.
- Root RAG/corpus helper scripts.
- Private/corpus-adjacent scripts and data.
- Landing/sign/brand assets and generated visual files.
- Historical untracked handoffs and screenshot/report assets.

Commit/staging rule:

- Do not use `git add .`.
- Do not broad-stage parked work.
- Stage only exact docs for this refresh if committing it.
- Do not stage runtime/backend/test/UI/source/corpus/deploy/auth/DNS/private/generated files unless a later exact-scope QA or Repo Steward task approves them.

## Blockers And Caveats

Blocking issues for protected-preview user smoke:

- None known after the `3a07c8f` protected-preview smoke.

Caveats to preserve:

- Root `/` redirects to `/ui/steel-guitar-rag-mock.html` and drops cache-bust query strings. Use direct `/ui/...?...` URLs for exact smoke.
- Current repo HEAD `f15ef6c` is a docs handoff commit after runtime commit `3a07c8f`. The served app code was verified at `3a07c8f`; that is expected because `f15ef6c` contains only the Lane 12 smoke handoff.
- Broad dirty/untracked work remains parked and should not be mixed with runtime/user-smoke tasks.
- Historical `Address already in use` traces remain in durable stderr logs; latest smoke indicates current launchd-owned process is healthy.

## Safe-To-Stage For This Refresh

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-23-01-final-deployment-user-smoke-status.md`

## Files Not To Stage For This Refresh

- Backend/runtime files, tests, UI files, deployment/launchd files, auth/DNS/Cloudflare config, tunnel files, source files, or app assets.
- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, generated corpus outputs, scraper output, source-inbox raw/provenance files.
- Deployment secrets, private env files, rendered plists, tunnel tokens, tunnel credentials, `.wrangler/`, and any secrets.
- `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, generated visual assets, and unrelated UI/assets.
- Unrelated handoffs or generated reports.

## Recommended Next Control Step

Protected preview is ready for user smoke.

Use these exact URLs after Cloudflare Access login:

```text
Main app:
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=3a07c8f

E9 Fretboard Explorer:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=3a07c8f
```

Route any new defects by lane:

- Lane 05 Backend / RAG Integration for answer routing, deterministic-answer, source-card, or API behavior issues.
- Lane 06 UX/UI Design for UI, fretboard, tab, Explorer, or rendering issues.
- Lane 11 Auth / Security for Cloudflare Access/auth/session issues.
- Lane 12 Self-Hosted Deployment for runtime, version, restart, log, tunnel, or deployment issues.
- Lane 15 QA / Answer Eval for regression matrix, smoke, or verification tasks.
