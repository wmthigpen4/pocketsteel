# E9 Explorer Integration Status Refresh

## Task Summary

Lane: 01 Repo Steward.

Requested: refresh the Steel Guitar RAG integration/status snapshot to reflect the current E9 harmony guidance and E9 Fretboard Explorer development state.

Completed:

- Read the requested E9 harmony, Explorer backend, UI, QA, protected-preview, tooltip/detail, and key-expansion handoffs.
- Inspected current branch, HEAD, dirty worktree, cached index, relevant Explorer source files, the harmony guidance document, and relevant tests.
- Updated `docs/handoffs/task-completions/integration-status.md` with a current top-level E9 Explorer / harmony guidance snapshot.
- Created this scoped status-refresh handoff.

Intentionally not changed:

- No app code.
- No tests.
- No corpus, Chroma/vector stores, embeddings, scraper output, source-inbox data, deployment, auth, DNS, secrets, assets, or private source data.

## Current Branch And HEAD

- Branch: `feature/answer-api`
- Current HEAD: `e90e157 feat: expand e9 fretboard explorer keys`

## Files Changed

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-22-e9-explorer-integration-status-refresh.md`

## Current E9 Explorer Status

- Deterministic Explorer backend exists in `pocketsteel/fretboard_explorer.py`.
- Backend Explorer logic is independent from RAG/corpus retrieval and uses pitch validation for musical truth.
- Initial G-focused MVP rows were implemented and tested.
- Learner-facing display fields were added and consumed by the UI.
- G natural minor display spelling uses `Bb` and `Eb` in learner-facing fields while canonical/internal validation remains unchanged.
- Browser-accessible Explorer surface exists at `/ui/e9-fretboard-explorer.html`.
- Explorer UI includes controls for key, scale, harmony/view, and string group.
- Current browser fixture/controller remains G-oriented even though the backend now supports additional keys.
- User-smoke UI fixes, cache-bust refreshes, and tooltip/detail UX passed protected-preview smoke.
- Latest protected-preview tooltip/detail URL:
  - `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-tooltip-detail-ux-20260622`

## Current Harmony Guidance Status

- `docs/llm-guidance/e9_harmonized_scales_and_diatonic_harmony_knowledge.md` exists.
- It was VTT-enhanced, conflict-audited, and cleaned up.
- It remains guidance material only.
- It has not been ingested, chunked, embedded, connected to Chroma, or wired into answer/retrieval behavior.

## Tests / Checks Reported By Recent Lanes

- Explorer backend slice: `784 passed`.
- UI display-field slice: `787 passed`.
- Browser surface: `790 passed`.
- User-smoke UI fixes / protected refresh / tooltip-detail UX: `791 passed`.
- Key expansion backend slice: `795 passed`.
- Current docs-only refresh checks are listed below.

## Checks Run In This Task

- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git log --oneline -20`
- `git diff --check`
- `git diff --cached --name-only`
- Source/handoff inspection commands for the requested files.

Pending after this handoff:

- `git diff --cached --check` and cached diff review before commit.

## Known Risks

- The backend key expansion at `e90e157` needs Lane 15 QA.
- Expanded keys are not yet exposed in the current G-oriented browser static fixture/controller.
- Harmony markdown should not be treated as structured runtime truth until table-wide pitch validation and ingestion design are approved.
- Broad unrelated dirty/untracked worktree remains parked.

## Human Decision Needed

No for this docs-only refresh.

Future decisions:

- Whether to expose all supported backend key spellings in UI or a reduced key selector.
- Whether/how to validate and ingest harmony guidance into corpus or curated guidance.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-22-e9-explorer-integration-status-refresh.md`

## Files That Must Not Be Staged

- Any unrelated dirty/untracked files.
- App code.
- Tests.
- Corpus/private corpus files.
- Chroma/vector stores.
- Embeddings.
- Scraper output.
- Source-inbox raw/provenance files.
- Deployment/auth/DNS/secrets files.
- `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, generated visual assets, and unrelated UI/assets.

## Recommended Next Lane

Lane 15 QA / Answer Eval.

Exact next prompt:

```text
Lane 15: QA the E9 Fretboard Explorer key expansion at HEAD e90e157. Verify G behavior is unchanged, representative C/D/F/Bb major rows validate, C natural minor display spelling uses flats, advanced swaps remain gated, pitch validation owns musical truth, and no UI/corpus/deployment/private-source files changed. Run focused Explorer tests and full pytest if practical. Write a QA handoff with exact safe-to-stage guidance if any docs are created.
```

## Commit Readiness

Safe to commit after exact-path staging and cached diff review.
