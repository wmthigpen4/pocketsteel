# 2026-06-23 E9 Explorer Integration Status Refresh

## Task Summary

Lane: 01 Repo Steward.

Requested: refresh the reset/guidance snapshot for the current E9 Fretboard Explorer state after expanded keys, explanation UI, tracked keyhead SVG, home-page entry, and protected-preview full app smoke.

Completed:

- Read the requested governance files, current integration snapshot, recent E9 Explorer handoffs, protected-preview smoke handoffs, and relevant source/test surfaces.
- Updated `docs/handoffs/task-completions/integration-status.md` so it no longer treats `e90e157` as the current Explorer state.
- Recorded current HEAD `abed6ff`, latest relevant commits, tracked SVG status, protected-preview smoke evidence, test status, and next-lane guidance.

Intentionally not changed:

- No app code.
- No tests.
- No UI files.
- No SVG or visual assets.
- No corpus, Chroma/vector stores, embeddings, scraper output, source-inbox data, deployment, auth, DNS, secrets, or private source data.

## Current State

- Branch: `feature/answer-api`
- Starting HEAD: `abed6ff fix: refresh e9 explorer home entry cache-bust`
- Current E9 Explorer state: committed and protected-preview smoked from the app page into `/ui/e9-fretboard-explorer.html`.
- Latest full app smoke URL: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=e9-explorer-home-entry-20260623`
- Latest full app smoke runtime evidence: local `/api/version` reported `git_sha: abed6ff`, branch `feature/answer-api`, retrieval mode `hybrid_private_first`, auth provider `cloudflare_access`.

## Files Changed

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-23-e9-explorer-integration-status-refresh.md`

## Current E9 Explorer Status

- Deterministic backend row generation exists in `pocketsteel/fretboard_explorer.py`.
- Expanded backend key support is implemented.
- Browser UI exposes the QA-covered keys: `G`, `C`, `D`, `F`, `Bb`, `Eb`.
- Key-aware display spelling is implemented.
- UI includes mode-aware string-group filtering, separated core/advanced groups, compact row buttons, selected-row detail panel, marker tooltip/detail UX, and deterministic explanation copy.
- Full app smoke verified app-page entry, Explorer navigation, expanded keys, explanation UI, tracked SVG route, mobile/narrow usability, and no object-string rendering.

## Current SVG Asset Status

- `public/brand/pedal-steel-fretboard-background.svg` is tracked.
- V-shaped keyhead/tuner layout was committed in `bce771f`.
- Protected-preview tracked-asset smoke passed in `2026-06-23-keyhead-vshape-tracked-asset-protected-smoke.md`.
- Known caveat: direct raw SVG tabs can emit a browser-runtime promise warning; Explorer page rendering remains normal.

## Current Corpus / Embedding Status

- `docs/llm-guidance/e9_harmonized_scales_and_diatonic_harmony_knowledge.md` exists and has been VTT-enhanced, conflict-audited, and cleaned up.
- It remains guidance only.
- It has not been ingested, chunked, embedded, connected to Chroma/vector stores, or wired into RAG/source-card behavior.

## Tests And Checks

Reported by recent lanes:

- Full pytest: `808 passed`.
- `tests/test_frontend_answer_ui.py -q`: `23 passed`.
- `tests/test_pedal_steel_fretboard_ui.py -q`: `31 passed`.
- `tests/test_fretboard_explorer.py -q`: `28 passed`.
- JS syntax checks passed for `ui/answer-client.js`, `ui/pedal-steel-fretboard.js`, `ui/e9-fretboard-explorer.js`, and `ui/e9-fretboard-explorer-data.js`.

Checks run for this docs-only refresh:

- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git log --oneline -25`
- `git diff --check`
- `git diff --cached --name-only`
- handoff/source inspection commands for the requested files

Pending before commit:

- `git diff --cached --name-only`
- `git diff --cached`
- `git diff --cached --check`

## Risks

- Broad unrelated dirty/untracked worktree remains parked.
- Bare root `/` was not certified by the latest full app smoke; the tested app URL remains `/ui/steel-guitar-rag-mock.html?v=e9-explorer-home-entry-20260623`.
- Mobile Explorer is usable but vertically dense.
- Harmony guidance must not be treated as runtime/corpus truth without a separate approved ingestion design.

## Human Decision Needed

No for this docs-only status refresh.

Future decisions:

- Whether to make bare root `/` the canonical Explorer demo entry and ask Lane 12 to certify it.
- Whether to polish mobile Explorer density.
- Whether to plan curated-guidance/harmony ingestion after user demo feedback.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-23-e9-explorer-integration-status-refresh.md`

## Files That Must Not Be Staged

- Any unrelated dirty/untracked files.
- App code, tests, UI files, SVG assets, source files, or scripts.
- Corpus/private corpus files.
- Chroma/vector stores.
- Embeddings.
- Scraper output.
- Source-inbox raw/provenance files.
- Deployment/auth/DNS/secrets files.
- `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, generated visual assets, and unrelated UI/assets.
- Parked closeout handoffs unless explicitly requested by a later task.

## Recommended Next Lane

User demo/smoke first, using:

```text
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=e9-explorer-home-entry-20260623
```

If root `/` should be certified as the demo entry, run Lane 12:

```text
Lane 12: Run ProtectedPreviewSmoke for the E9 Fretboard Explorer app entry at current HEAD. Verify /api/version, root `/` behavior, and the canonical app URL. Test https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=e9-explorer-home-entry-20260623 plus /ui/e9-fretboard-explorer.html. Confirm Cloudflare Access login succeeds, the home entry opens the Explorer, expanded keys and explanations work, the tracked SVG asset loads, and no [object Object], E-lower+E-lower, or raw validated-row-count primary copy appears.
```

## Commit Readiness

Safe to commit after exact-path staging and cached diff review.
