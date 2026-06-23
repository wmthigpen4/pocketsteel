# 2026-06-23 06 Five Eight Label Leak Fix

## Task Summary
- Lane: 06 UX/UI Design.
- Requested: remove the learner-facing raw `five_eight_branch` label leak from the E9 Fretboard Explorer while preserving the human-facing `5&8 branch positions` option and `5-8` selectable/filterable behavior.
- Completed: sanitized the shared fretboard renderer's learner-facing metadata text so exact `five_eight_branch` values render as `5&8 branch`, added a regression test, and refreshed the Explorer page's `pedal-steel-fretboard.js` cache-bust so protected preview loads the fixed renderer.
- Intentionally not changed: backend harmonic-scale rules, tab engine behavior, answer routing/source behavior, deployment/launchd files, Cloudflare/DNS/auth/tunnel configuration, corpus, Chroma, embeddings, private source data, and unrelated dirty work.

## Status
- Pass/warn/fail: Pass.
- Branch: `feature/answer-api`.
- Starting HEAD: `fe40292`.
- Final HEAD at handoff write time: `fe40292` before the scoped commit; final commit should be reported in the closeout.
- UI code changed: Yes.
- Raw `five_eight_branch` learner-facing UI status: fixed in the shared fretboard card/detail rendering path.
- `5&8 branch positions` status: still present in the Explorer harmony/view selector.
- `5-8` selectable/filterable status: unchanged; remains selectable/filterable when validated rows exist.

## Files Inspected
- `AGENTS.md`
- `agents.md`
- `PLAN.md` (missing)
- `plan.md` (missing)
- `README.md`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-23-06-g-five-eight-ui-labels.md`
- `docs/handoffs/task-completions/2026-06-23-12-launchdaemon-final-protected-smoke.md`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer-data.js`
- `ui/pedal-steel-fretboard.js`
- `tests/test_frontend_answer_ui.py`
- `tests/test_pedal_steel_fretboard_ui.py`
- `tests/test_fretboard_explorer.py`

## Files Changed
- `ui/pedal-steel-fretboard.js`
  - Added learner-facing metadata sanitization for exact `five_eight_branch` values.
  - This catches selector-card reason text, detail fields, and normalized position-kind/tier-reason rendering.
- `ui/e9-fretboard-explorer.html`
  - Bumped the Explorer page's `pedal-steel-fretboard.js` query string to `five-eight-label-leak-fix-20260623` so the protected preview fetches the fixed renderer.
- `tests/test_pedal_steel_fretboard_ui.py`
  - Added a regression test proving raw `five_eight_branch` in `tierReason` and `positionKind` renders as `5&8 branch` and does not appear in generated fretboard card/detail HTML.
- `tests/test_frontend_answer_ui.py`
  - Updated the Explorer HTML assertion for the refreshed fretboard renderer cache-bust.
- `docs/handoffs/task-completions/2026-06-23-06-five-eight-label-leak-fix.md`
  - This handoff.

## Exact Leak Location
- The leak came from the shared renderer in `ui/pedal-steel-fretboard.js`.
- Explorer passes branch rows into `mountPedalSteelFretboard()`.
- `normalizePosition()` preserved `tierReason: "five_eight_branch"` / `positionKind: "five_eight_branch"`.
- `renderPositionTools()` builds selector-card text with `positionCardReason(highlight)`.
- `positionCardReason()` selected `highlight.tierReason`, producing visible text like `advanced: ... five_eight_branch ...`.

## Fix Details
- Added `learnerFacingMetadataText()` and applied it in `formatDetailValue()` for primitive values.
- Exact `five_eight_branch` values now render as `5&8 branch` in learner-facing text.
- Internal payload/filter metadata may still use `five_eight_branch` where needed for deterministic filtering.
- The Explorer page cache-bust now forces the fixed shared renderer to load in protected preview.

## Tests And Checks Run
- `git status --short` — broad unrelated dirty/untracked work confirmed and left untouched.
- `git diff --cached --name-only` — no staged files at task start.
- `git diff --check` — passed.
- `git branch --show-current` — `feature/answer-api`.
- `git rev-parse --short HEAD` — `fe40292`.
- `git log -1 --oneline` — `fe40292 docs: record final launchdaemon protected smoke`.
- `git log --oneline -12` — inspected.
- `node --check ui/e9-fretboard-explorer.js` — passed.
- `node --check ui/e9-fretboard-explorer-data.js` — passed.
- `node --check ui/answer-client.js` — passed.
- `node --check ui/pedal-steel-fretboard.js` — passed.
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` — `23 passed`.
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` — `32 passed`.
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` — `30 passed`.
- Direct Node render check using real Explorer G `five_eight_branch` rows and real fretboard renderer — `{"rows":4,"hasFriendly":true,"hasRaw":false}`.

## Integration Notes
- This is a display/UI fix only. Backend payload values remain unchanged.
- The raw token is still allowed in internal JSON and filter keys. The blocked condition is learner-facing rendered text.
- Protected-preview smoke was intentionally not run in Lane 06 per task constraints.

## Risk Assessment
- Risk: Low.
- Reason: The code change is a small exact-token display sanitizer and a page-local cache-bust update, covered by focused component tests and a direct render check.
- Rollback: revert the scoped commit.

## Human Decision Needed
- No.

## Safe-To-Stage Exact File List
- `ui/pedal-steel-fretboard.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_pedal_steel_fretboard_ui.py`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-23-06-five-eight-label-leak-fix.md`

## Files That Must Not Be Staged
- Any corpus, Chroma/vector, embeddings, scraper output, deployment/launchd, auth/DNS/tunnel/private-data files.
- Existing unrelated dirty files shown by `git status --short`, including `README.md`, corpus metadata, RAG scripts, source-inbox files, landing/sign assets, and unrelated untracked handoffs/assets.

## Recommended Next Lane
- Lane 12 Self-Hosted Deployment / protected-preview smoke.

## Commit Readiness
- Safe to commit after exact-path staging, staged diff review, and `git diff --cached --check`.

## Suggested Next Step
- Lane 12: run protected-preview smoke against the launchd-supervised runtime and verify both the main app and Explorer at `/ui/e9-fretboard-explorer.html`; specifically confirm `5&8 branch positions` and `5-8` still work and raw `five_eight_branch` no longer appears in visible row/card text.
