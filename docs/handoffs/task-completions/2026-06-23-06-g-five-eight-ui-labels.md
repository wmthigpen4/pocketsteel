# 2026-06-23 06 G Five Eight UI Labels

## Task Summary
- Lane: 06 UX/UI Design.
- Requested: expose/select/filter the new deterministic G 5&8 Explorer branch added by backend commit `c08cc95`, avoid raw learner-facing `five_eight_branch` metadata, and preserve existing Explorer behavior.
- Completed: added a user-facing `5&8 branch positions` harmony option, scoped `5-8` string-group filtering, friendly `5&8 branch` labels in cards/details, refreshed the static Explorer browser fixture from the backend payload builder, and bumped Explorer JS/data cache-busts.
- Intentionally not changed: backend rules, tab engine behavior, source/copyright guardrails, deployment/protected-preview smoke, corpus, scraping, embeddings, Chroma, auth/DNS, private data, and unrelated dirty work.

## Status
- Pass/warn/fail: Pass.
- Branch: `feature/answer-api`.
- Starting HEAD: `daa0adc`.
- Final HEAD at handoff write time: `daa0adc` before the scoped commit; post-commit HEAD should be reported by Repo Steward/final response.
- UI code changed: Yes.
- Raw internal metadata in visible UI: No. `five_eight_branch` remains in payload/data attributes for deterministic filtering, but visible labels render as `5&8 branch` / `5&8 branch positions`.
- `5-8` selectable/filterable: Yes, when the selected key/scale/harmony has validated rows. G major exposes `5&8 branch positions` and a `5-8` string group; non-row combinations stay unavailable rather than showing an empty branch selector.

## Files Inspected
- `AGENTS.md`
- `agents.md`
- `PLAN.md` (missing)
- `plan.md` (missing)
- `README.md`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-23-05-g-harmonized-scale-deterministic-rules.md`
- `docs/handoffs/task-completions/2026-06-23-15-g-harmonized-scale-qa.md`
- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer-data.js`
- `tests/test_frontend_answer_ui.py`
- `tests/test_pedal_steel_fretboard_ui.py`
- `tests/test_fretboard_explorer.py`

## Files Changed
- `ui/e9-fretboard-explorer.js`
  - Added `FIVE_EIGHT_GROUPS`.
  - Added `five_eight_branch` harmony matching.
  - Added `All 5&8 branch positions` / `5&8 branch` labels.
  - Kept branch rows out of two-string and three-string modes.
- `ui/e9-fretboard-explorer.html`
  - Added the `5&8 branch positions` harmony option.
  - Bumped Explorer data/controller cache-busts to `g-five-eight-ui-20260623`.
- `ui/e9-fretboard-explorer-data.js`
  - Regenerated static browser fixture from `steel_guitar_rag.fretboard_explorer.build_explorer_payload(key)`.
  - Includes the validated G major `five_eight_branch` rows for string group `5-8`.
- `tests/test_frontend_answer_ui.py`
  - Added assertions for the new harmony option, refreshed cache-busts, G payload branch rows, `5-8` filtering, and visible-label guardrails.
- `docs/handoffs/task-completions/2026-06-23-06-g-five-eight-ui-labels.md`
  - This handoff.

## Tests And Checks Run
- `git status --short` — broad unrelated dirty/untracked work confirmed and left untouched.
- `git diff --cached --name-only` — no staged files at task start.
- `git diff --check` — passed before edits and after focused checks.
- `git branch --show-current` — `feature/answer-api`.
- `git rev-parse --short HEAD` — `daa0adc`.
- `git log -1 --oneline` — `daa0adc docs: record launchdaemon final smoke`.
- `node --check ui/e9-fretboard-explorer.js` — passed.
- `node --check ui/e9-fretboard-explorer-data.js` — passed.
- `node --check ui/answer-client.js` — passed.
- `node --check ui/pedal-steel-fretboard.js` — passed.
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` — `23 passed`.
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` — `31 passed`.
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` — `30 passed`.

## Integration Notes
- The UI remains row-driven: the branch mode is only enabled when validated rows exist for the active key/scale. This avoids exposing a dead `five_eight_branch` mode for expanded keys whose metadata advertises the type but whose payload has no rows.
- The branch is separate from existing core/advanced three-string groups and existing two-string groups.
- The static browser fixture was stale; refreshing it was required for the browser route to have the new G 5&8 rows.
- Protected-preview smoke was intentionally not run per task constraints. If this commit lands, Lane 12 should refresh protected preview and verify `/ui/e9-fretboard-explorer.html` with the new cache-busts.

## Risk Assessment
- Risk: Low to medium.
- Reason: Runtime logic change is small and covered by focused VM/frontend tests, but the static data fixture regeneration is large because it reflects the current backend payload builder output.
- Rollback: revert the scoped commit; no backend or persistent data changes were made.

## Human Decision Needed
- No.

## Safe-To-Stage Exact File List
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer-data.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-23-06-g-five-eight-ui-labels.md`

## Files That Must Not Be Staged
- Any corpus, Chroma/vector, embeddings, scraper output, auth/DNS/deployment/private-data files.
- Existing unrelated dirty files shown by `git status --short`, including but not limited to `README.md`, corpus metadata, RAG scripts, `source-inbox/inventory.json`, landing/sign assets, and unrelated untracked handoffs/assets.

## Recommended Next Lane
- Lane 12 Self-Hosted Deployment / protected-preview smoke after this scoped UI commit.

## Commit Readiness
- Safe to commit after exact-path staging, staged diff review, and `git diff --cached --check`.

## Suggested Next Step
- Lane 12: refresh protected-preview cache/runtime and browser-smoke `/ui/e9-fretboard-explorer.html` for G major -> `5&8 branch positions` -> `5-8`.
