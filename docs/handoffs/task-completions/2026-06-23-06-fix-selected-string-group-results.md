# 2026-06-23 - Lane 06 - Fix Selected String Group Results

## Task Summary

Requested fix: the E9 Fretboard Explorer showed SVG markers for a selected state such as A major / 3-string diatonic harmony / 6-8-10, but the selected string-combination results were not visible/readable in the active fretboard area.

Completed:
- Added a compact selected-results strip inside the Explorer fretboard panel, above the SVG.
- The selected-results strip renders one button per currently filtered row and names the active string group, such as `6-8-10: 5 visible positions`.
- The strip uses the same filtered row set as the SVG highlights and the below-fretboard row list.
- The below-fretboard row list now includes the explicit string group in each row button meta line.
- Selected row state now syncs across the in-panel selected-results strip, the existing row list, the detail panel, and SVG marker interactions.
- Bumped the Explorer script/data/fretboard cache-bust to `selected-group-results-20260623`.

Intentionally not changed:
- No backend deterministic Explorer rules.
- No answer routing.
- No corpus, Chroma, embeddings, scraping, auth, DNS, tunnel, launchd, secrets, or private-source files.
- No fretboard geometry changes.
- No SVG asset changes.

## Root Cause

Matching rows were present and the SVG highlights mounted correctly, but the readable row/card list lived below the fretboard panel. In the user-smoke viewport, this made the selected string combinations look absent even though the markers were present. The row list also only labeled matching entries as `Core grip`, so the selected group such as `6-8-10` was not obvious in the card text.

## Files Changed

- `ui/e9-fretboard-explorer.html`
  - Added `#explorer-active-results` inside the fretboard panel.
  - Added compact horizontal selected-results CSS.
  - Bumped Explorer script cache-busts to `selected-group-results-20260623`.
- `ui/e9-fretboard-explorer.js`
  - Added selected group label helper.
  - Added `renderActiveResults()`.
  - Synchronized active selected-result buttons in `selectRow()`.
  - Added string-group labels to detailed row-list metadata.
- `tests/test_frontend_answer_ui.py`
  - Added assertions for `#explorer-active-results`.
  - Added regression coverage for A major / 3-string / 6-8-10.
  - Asserted active cards, row list, selected detail, and SVG highlight counts stay non-empty and aligned.

Generated artifacts: none.

Deleted files: none.

## Tests And Checks

Commands run:

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
git log -10 --oneline
git diff --cached --name-only
git diff --check
node --check ui/e9-fretboard-explorer.js
node --check ui/e9-fretboard-explorer-data.js
node --check ui/answer-client.js
node --check ui/pedal-steel-fretboard.js
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
```

Results:
- `node --check ui/e9-fretboard-explorer.js`: passed
- `node --check ui/e9-fretboard-explorer-data.js`: passed
- `node --check ui/answer-client.js`: passed
- `node --check ui/pedal-steel-fretboard.js`: passed
- `tests/test_frontend_answer_ui.py -q`: 23 passed
- `tests/test_pedal_steel_fretboard_ui.py -q`: 32 passed
- `tests/test_fretboard_explorer.py -q`: 32 passed
- `git diff --check`: passed

## Browser Smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?access=beta_user&v=selected-group-render-smoke`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?access=beta_user&v=selected-group-render-smoke`
- Exact URL the user should use: protected preview should use `/ui/e9-fretboard-explorer.html?v=selected-group-results-20260623` after Lane 12 refresh/restart
- Auth required: no for local smoke
- Auth provider: none for local smoke
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `94fc745` before commit
- Version endpoint: not checked for local smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local working tree and browser-loaded cache-busted Explorer HTML
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not relevant to this smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not relevant to this smoke
- Who should test this URL: Codex locally, Lane 12/Lane 15 on protected preview
- Do not test these URLs: production or Cloudflare/DNS targets for this Lane 06 task
- Known caveats: local browser smoke proves local rendering only; protected-preview requires Lane 12 refresh/smoke.

Smoke result:
- A major / 3-string diatonic harmony / `6-8-10` showed 5 active selected-result cards.
- The active selected-result cards all reported `6-8-10`.
- The below-fretboard row list showed 5 rows and all reported `6-8-10`.
- The SVG showed 5 highlight markers.
- Active selected-result IDs matched SVG highlight IDs.
- Switching to `5-6-8` showed 5 cards/highlights.
- Switching back to `6-8-10` showed 5 cards/highlights.
- Switching to 2-string view and back to 3-string view remained non-empty.
- No browser console errors were reported.
- No `[object Object]` was reported.
- No raw `five_eight_branch` text was reported.

## Integration Notes

- The selected-results strip is a UI-only reflection of the already-filtered deterministic Explorer rows.
- It does not create or infer rows; it reuses `getRows()`.
- The selected-results strip and SVG highlights share the same filtered row collection.
- The cache-bust update is needed so protected-preview browsers fetch the changed Explorer renderer.

## Risk Assessment

Risk: low.

Reason:
- Scope is limited to Explorer UI rendering and focused frontend tests.
- No backend or payload schema changes.
- No data generation changes.
- The existing detailed row list remains in place below the SVG.

Rollback note:
- Revert the changes in `ui/e9-fretboard-explorer.html`, `ui/e9-fretboard-explorer.js`, and `tests/test_frontend_answer_ui.py`.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-23-06-fix-selected-string-group-results.md`

## Files That Must Not Be Staged

All unrelated dirty or untracked files, including:
- corpus/private/source-inbox files
- Chroma/vector/embedding outputs
- raw or generated visual assets outside this scoped change
- unrelated docs and parked implementation files already present in the worktree
- `docs/handoffs/task-completions/integration-status.md`

## Recommended Next Lane

Lane 12 protected-preview smoke, then Lane 15 focused QA for the selected string-group rendering fix.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 12: refresh/restart protected preview and smoke `/ui/e9-fretboard-explorer.html?v=selected-group-results-20260623`, verifying A major / 3-string diatonic harmony / `6-8-10` shows visible selected-result cards and matching SVG highlights.
