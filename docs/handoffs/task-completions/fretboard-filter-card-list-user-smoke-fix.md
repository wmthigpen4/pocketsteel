# Fretboard Filter Card List User Smoke Fix

## Task Summary

Requested:

- Fix the fretboard filter bug where the top filters changed the fretboard display but the position cards below the fretboard still showed unrelated positions.
- Keep the fix frontend-only unless backend metadata was insufficient.
- Do not change `/api/answer`, backend routing, deployment, auth, corpus, Chroma/vector stores, scraping, source data, or visual assets.

Completed:

- Centralized runtime filter visibility into one shared DOM sync path for position cards, selected detail cards, SVG highlights, and legend entries.
- Added defensive `style.display = "none"` alongside `hidden` for hidden learner-facing position elements.
- Kept grip multi-select behavior.
- Made `All positions` clear active grip filters so it restores the full card set instead of leaving a narrowed grip filter active.
- Added focused regression assertions for the shared visibility path and G-major grip filtering behavior.

Intentionally not changed:

- No backend files, `/api/answer` schema, answer routing, deployment, auth, corpus, Chroma/vector stores, embeddings, source-inbox data, source data, or visual assets were changed.
- Existing unrelated dirty answer-card layout work remains parked.

## Root Cause

The component had multiple places updating visibility state. Cards, details, highlights, and legends could drift because runtime filtering set attributes directly across mixed element types rather than deriving one visible position-id set and applying it consistently everywhere.

The protected-preview symptom was that filter controls could appear to affect fretboard highlights while the below-fretboard card list still looked like an unfiltered large position dump.

## Files Changed

Changed:

- `ui/pedal-steel-fretboard.js`
- `tests/test_pedal_steel_fretboard_ui.py`

Created:

- `docs/handoffs/task-completions/fretboard-filter-card-list-user-smoke-fix.md`

Deleted:

- None.

## Exact Filter-State Fix

Implementation changes:

- Added `setPositionElementFilterVisibility(element, isVisible)`.
- Added `syncPositionElementVisibility(figure, visibleIds)`.
- Updated `updatePositionFilter(...)` to compute a single `visibleIds` set from visible selector cards.
- Applied that same `visibleIds` set to:
  - `[data-position-selector]`
  - `[data-position-detail]`
  - `.pedal-steel-fretboard__highlight`
  - `[data-legend-id]` when the legend item maps to a position selector
- Updated selected detail behavior so a visible filtered card becomes the selected detail after every filter change.
- Updated the `All positions` voicing control to clear active grip filters.

## Tests And Checks

Run:

```bash
git diff --check
node --check ui/answer-client.js
node --check ui/pedal-steel-fretboard.js
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py::test_filter_interaction_source_resets_hidden_selection_to_first_visible tests/test_pedal_steel_fretboard_ui.py::test_grip_filters_support_multi_select_and_filter_all_visible_outputs tests/test_frontend_answer_ui.py -q
```

Results:

- `git diff --check`: passed.
- `node --check ui/answer-client.js`: passed.
- `node --check ui/pedal-steel-fretboard.js`: passed.
- Focused pytest command: `21 passed`.

Also run:

```bash
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py tests/test_frontend_answer_ui.py -q
```

Result:

- `47 passed / 1 failed`.
- The failure is unrelated to this filter-card fix: `test_demo_page_mounts_the_component_without_touching_landing_pages` still expects `ui/pedal-steel-fretboard-demo.html`, which is absent in the current worktree.
- This task did not create or modify the standalone demo page.

## Browser Smoke Target

Smoke Target:
- Target type: local
- Result type: browser smoke with stubbed local API responses
- Exact browser URL tested: `http://127.0.0.1:8798/ui/steel-guitar-rag-mock.html`
- Cache-busted URL tested: `http://127.0.0.1:8798/ui/steel-guitar-rag-mock.html?access=beta_user&v=fretboard-filter-card-list-local-rerun`
- Exact URL the user should test: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=fretboard-filter-card-list-<commit>` after Cloudflare Access login and Lane 12 protected-preview verification
- Auth required: local no; protected preview yes
- Auth provider: local none/scaffold; protected preview Cloudflare Access
- Cloudflare Access login result: not attempted
- Local backend URL: `http://127.0.0.1:8798`
- Expected backend port: `8798`
- Expected git HEAD: pre-commit working tree based on `256b3be`
- Version endpoint result: stubbed local smoke only
- Root URL status: not used as proof
- API fallback status: not used; this was local browser smoke with stubbed API responses
- Known caveats: local smoke does not prove protected-preview behavior

## Browser Smoke Result

Prompt:

- `How do I play a G chord on the E9?`

Before:

- Protected-preview user smoke reported a broad unfiltered card dump after selecting grip `3-4-5`.
- Exact protected-preview before count was not available from the report; the observed behavior was many unrelated cards still visible.

After local browser smoke:

| Filter state | Visible card count | Result |
| --- | ---: | --- |
| Default recommended | 5 | Passed; recommended cap still limited the default set |
| Grip `3-4-5` | 2 | Passed; every visible card was grip `3-4-5` |
| Grip `4-5-6` | 2 | Passed; every visible card was grip `4-5-6` |
| Root position + grip `3-4-5` | 1 | Passed; selected detail matched visible grip `3-4-5` |
| All positions | 6 | Passed; grip filters cleared and full stubbed position set returned |

Additional smoke checks:

- SVG highlights matched the visible card set.
- Selected detail never pointed at a hidden card.
- No object-string rendering was detected.
- No raw source/forum fragment was detected.

## Integration Notes

- This is a frontend-only runtime filter synchronization fix.
- Protected preview was not restarted.
- After commit, update `integration-status.md` separately and ask Lane 12 to verify protected preview from this commit or later.

Schema/API/component/data contract changes:

- No API/schema changes.
- Component behavior changes: filter visibility now has one shared DOM sync path, and `All positions` clears grip filters.

Assumptions:

- The backend position payload already has enough grip/voicing metadata.
- Protected-preview user smoke is blocked until Lane 12 verifies the committed fix on the canonical UI path.

Blockers:

- Protected-preview verification remains.
- The unrelated standalone fretboard demo test gap remains parked.

## Risk Assessment

Risk: low to medium.

Why:

- The fix is scoped to the fretboard component runtime filtering.
- It deliberately changes browser DOM visibility behavior, the exact area being reported.
- Focused tests and local browser smoke passed.

Rollback:

- Revert the implementation commit if protected-preview smoke shows a card/filter regression.

## Commit Readiness

Safe to commit

## Suggested Next Step

Recommended lane: `12 Self-Hosted Deployment`.

Exact prompt:

```text
LANE: 12 Self-Hosted Deployment
REASONING: MEDIUM
Branch: feature/answer-api

Restart or verify protected-preview runtime from the fretboard filter card-list commit or later.

Smoke Target:
- Target type: protected-preview
- Exact browser URL: https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html
- Cache-busted URL: https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=fretboard-filter-card-list-<commit>
- Auth required: yes
- Auth provider: Cloudflare Access
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: fretboard filter card-list commit or later
- Version endpoint result: record if available
- Root URL status: do not assume root works unless verified
- API fallback status: not sufficient for this UI filter verification
- Exact URL the user should test: https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=fretboard-filter-card-list-<commit> after Cloudflare Access login

Verify:
- `How do I play a G chord on the E9?` shows the fretboard.
- Selecting grip `3-4-5` shows only `3-4-5` cards below the fretboard.
- Selecting grip `4-5-6` shows only `4-5-6` cards below the fretboard.
- Root position + grip `3-4-5` shows only cards matching both filters.
- `All positions` clears grip filters and restores the full advanced card set.
- Selected detail always points at a visible filtered card.
- No object-string rendering, raw source fragments, or weak-source primary warning.
```
