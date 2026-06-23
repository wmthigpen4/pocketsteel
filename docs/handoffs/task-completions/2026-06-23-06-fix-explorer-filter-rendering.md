# 2026-06-23 Lane 06 - Fix Explorer Filter Rendering

## Pass/Warn/Fail

Pass.

## Branch And HEAD

- Branch: `feature/answer-api`
- Starting HEAD: `e83e0e7`
- Final HEAD / commit hash if committed: pending at handoff write time

## Task Summary

Requested: fix the E9 Fretboard Explorer regression after `f2581f8` where user smoke reported misaligned controls, 5&8 appearing like an orphan group, and blank fretboard/card rendering.

Completed:

- Reproduced the Explorer states locally through browser automation.
- Confirmed the current local files render non-empty results, but also confirmed the HTML still referenced the old `explorer-ui-cleanup-20260623` script query after the previous JS/layout change.
- Updated Explorer script cache-busts to `explorer-render-fix-20260623` so protected-preview/user browsers fetch the current Explorer renderer/data/fretboard scripts.
- Aligned Key, Scale, and Harmony/View selects to identical top-row sizing.
- Hardened String Group option rebuilding so invalid stale selections are dropped when switching Harmony/View.
- Preserved String Group as a multi-select.
- Kept 5-8 inside the `2-string groups` optgroup for the 2-string harmonized-scale view.
- Preserved learner-facing 5&8 branch and Advanced swaps explanation.

Intentionally not changed:

- Backend deterministic E9 rules.
- Explorer payload/data rows.
- Answer routing.
- Auth, DNS, launchd, tunnel, corpus, Chroma, embeddings, scraping, secrets, or private-source files.

## Exact Root Cause

The blank protected/user render was consistent with a stale script fetch: `ui/e9-fretboard-explorer.html` still loaded:

- `pedal-steel-fretboard.js?v=explorer-ui-cleanup-20260623`
- `e9-fretboard-explorer-data.js?v=explorer-ui-cleanup-20260623`
- `e9-fretboard-explorer.js?v=explorer-ui-cleanup-20260623`

after the previous Explorer JS/layout change. That left protected-preview/user browsers able to keep running cached Explorer JavaScript against newer HTML. The fix refreshes all three Explorer script query strings.

The layout issue was separate: the top control grid stretched unevenly because only Key carried helper copy in the compact row. The fix pins compact selects to 42px and aligns control content to the top.

The filter-state issue was proactively hardened: when switching between 2-string and 3-string views, String Group now intersects current selections with groups valid for the new view before rendering. If no valid selection remains, it resets to All.

## Files Changed

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-23-06-fix-explorer-filter-rendering.md`

## What Changed

### Control Alignment

- Added `align-content: start` to Explorer controls.
- Set compact non-multi-select controls to `height: 42px`.
- Verified Key, Scale, and Harmony/View all render at the same y-position and height in local browser smoke.

### Rendering / Filter State

- Added `availableStringGroups(rows, harmony)`.
- `updateStringGroupOptions()` now drops incompatible selections before rebuilding the multi-select.
- Switching from 2-string `5-8` back to 3-string diatonic resets String Group to `all` and renders non-empty cards/highlights.

### 5&8 Grouping

- 5-8 remains in the 2-string harmonized-scale context.
- 5-8 appears inside the `2-string groups` optgroup, not a separate 5&8 optgroup.
- Raw `five_eight_branch` remains internal and did not appear in local browser body text.

## Local Browser Smoke Result

```text
Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?access=beta_user&v=explorer-render-fix
- Cache-busted URL tested: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?access=beta_user&v=explorer-render-fix
- Exact URL the user should use: protected-preview cache-busted URL after Lane 12 refresh
- Auth required: no for local smoke
- Auth provider: none for local smoke
- Cloudflare Access login result: not required
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: e83e0e7 plus local scoped changes
- Version endpoint: not checked for this local smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local DOM/script inspection
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not relevant to this Explorer-only smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not relevant to this Explorer-only smoke
- Who should test this URL: Codex locally; Lane 12 should test protected preview after commit
- Do not test these URLs: production URLs for this local UI slice
- Known caveats: local smoke does not prove protected-preview cache freshness
```

Verified:

- Default G major / 3-string diatonic harmony: 34 cards and 34 SVG highlights.
- G major / 2-string harmonized scale: 44 cards and 44 SVG highlights.
- 5-8 selected in 2-string view: 4 cards and 4 SVG highlights.
- Switching from 5-8 back to 3-string diatonic harmony: resets to All and shows 34 cards and 34 SVG highlights.
- Key, Scale, and Harmony/View selects all measured `42px` high and aligned at the same y-position.
- 5-8 appears inside `2-string groups`.
- No raw `five_eight_branch`.
- No relevant console warnings or errors.

## Tests And Checks

Passed:

- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/e9-fretboard-explorer-data.js`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q`
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q`

Pending at handoff write time:

- `git diff --check`
- staged diff review before commit

## Risks

Risk: low.

The changes are limited to Explorer UI cache-busting, select layout, and frontend filter-state handling. No backend or payload logic changed.

Remaining risk: protected-preview can still show stale assets until Lane 12 restarts/refreshes runtime and smokes a fresh cache-busted Explorer URL.

## Blockers

None for this UI slice.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-23-06-fix-explorer-filter-rendering.md`

## Files That Must Remain Unstaged

- Existing unrelated modified files, including `README.md`, corpus metadata/docs, RAG scripts, `source-inbox/inventory.json`, and landing-sign assets.
- Existing unrelated untracked docs, data, public/brand, ui/brand, source-inbox, Neon Sign, generated reports, and private/generated files.

## Recommended Next Lane

Lane 15 focused QA for Explorer rendering/filter state, then Lane 12 protected-preview smoke.

## Commit Readiness

Safe to commit after `git diff --check`, exact-path staging, cached diff review, and `git diff --cached --check`.

## Suggested Next Step

Lane 15 prompt: run focused Explorer QA for default render, 3-string render, 2-string render, 5-8 selection, switching from 5-8 back to 3-string, aligned Key/Scale/Harmony controls, 5-8 grouping, and no `five_eight_branch` leakage.
