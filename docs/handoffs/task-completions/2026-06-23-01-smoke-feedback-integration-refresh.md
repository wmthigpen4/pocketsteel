# Smoke Feedback Integration Refresh

Pass/warn/fail: warn

Branch: `feature/answer-api`

Starting HEAD: `08221a6 docs: complete smoke feedback protected preview`

Final HEAD / commit if committed: pending at handoff creation

## Task Summary

Repo Steward refreshed the reset/status documentation after Lane 12 completed authenticated protected-preview browser smoke for the smoke-feedback slice.

Completed:
- Updated `docs/handoffs/task-completions/integration-status.md`.
- Recorded latest protected-preview smoke commit `08221a6`.
- Recorded protected-preview runtime `1c0bbd6`.
- Recorded protected-preview status as pass with warnings.
- Preserved the three Lane 12 warnings and routed them by lane.
- Recorded direct cache-busted main app and Explorer URLs.

Intentionally not changed:
- No backend, UI, deployment, auth, DNS, corpus, Chroma/vector store, embeddings, scraping, private-source, source-inbox, paid transcript, or design-asset files.
- No protected-preview restart.
- No protected-preview smoke rerun.
- No unrelated dirty/untracked files staged.

## Files Changed

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-23-01-smoke-feedback-integration-refresh.md`

## Warnings Preserved

1. Root URL drops cache-bust and may show stale prompt chips.
2. `Show me a G major grip.` exposes `tab_example_event` / `Tab event` wording in fretboard detail.
3. Ab/A-flat prose normalizes correctly, but fretboard card labels canonicalize the enharmonic chord as `G# major`.

## Defect Routing

- Root cache-bust behavior: Lane 12 Self-Hosted Deployment.
- `tab_example_event` / `Tab event` wording: Lane 05 if the API payload/detail contract owns the wording; Lane 06 if this is only display-label handling.
- Ab/A-flat canonicalization to `G# major` fretboard labels: Lane 05 Backend / RAG Integration.

## Final Status

- Protected-preview status: pass with warnings.
- Cloudflare Access: succeeded in Lane 12 smoke.
- Main app: loaded and prompt matrix passed except warnings.
- Explorer: loaded and passed.
- User smoke: allowed if warnings are acceptable; not a clean pass.
- App can be parked with known warnings, or a follow-up warning slice can be opened.

## Checks Run

- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git log -10 --oneline`
- `git diff --name-only`
- `git diff --cached --name-only`
- `git diff --check`

Staged checks are expected to be run by Repo Steward before commit:

- `git diff --cached --name-only`
- `git diff --cached`
- `git diff --cached --check`

## Risks

Risk: low.

Reason:
- This is a docs-only integration refresh.
- It records already-completed Lane 12 protected-preview verification.
- It does not convert the smoke result into a clean pass.

## Blockers

No hard protected-preview blocker is known from the latest Lane 12 smoke.

Warnings remain and are routed above.

## Unrelated Parked Files

Broad dirty/untracked work remains parked, including:

- README/docs/provenance/legal/source-policy edits.
- Corpus metadata and source-inbox metadata.
- Root RAG/corpus helper scripts.
- Private/corpus-adjacent scripts and data.
- Landing/sign/brand assets and generated visual files.
- Historical untracked handoffs and screenshot/report assets.

## Human Decision Needed

No.

The user can either park the app with known warnings or choose one follow-up warning slice.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-23-01-smoke-feedback-integration-refresh.md`

## Files That Must Not Be Staged

- Backend/runtime files, tests, UI files, deployment/launchd files, auth/DNS/Cloudflare config, tunnel files, source files, paid transcript files, or app assets.
- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, generated corpus outputs, scraper output, source-inbox raw/provenance files.
- Deployment secrets, private env files, rendered plists, tunnel tokens, tunnel credentials, `.wrangler/`, and any secrets.
- `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, generated visual assets, and unrelated UI/assets.
- Unrelated handoffs or generated reports.

## Recommended Next Lane

None if the app is parked with known warnings.

If warnings are promoted:
- Lane 12 for root cache-bust/redirect behavior.
- Lane 05 for API payload/detail contract wording and Ab/A-flat backend canonicalization.
- Lane 06 for display-label-only cleanup if payloads are already correct.
- Lane 15 for regression matrix or smoke QA.

## Commit Readiness

Safe to commit as docs-only if staged diff contains only the two safe-to-stage files and staged diff checks pass.
