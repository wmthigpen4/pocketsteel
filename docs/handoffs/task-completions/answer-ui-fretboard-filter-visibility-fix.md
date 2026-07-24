# Answer UI Fretboard Filter Visibility Fix

- Branch: `feature/answer-api`
- HEAD: `77ff8f6`
- Lane: `06 UX/UI Design`
- Date: 2026-06-13
- Commit readiness: `Safe to commit`

## Task Summary

Requested a narrow frontend fix for the QA-blocking fretboard/filter UI issue before user smoke testing.

QA found that answer content and non-fretboard prompts were clean, but browser-rendered fretboard answers showed `0` visible cards/details in the default `Recommended` view. `Starter` and `Full chord` could also hide all cards, while `All positions` and grip-only filtering worked.

Completed:

- Fixed the DOM-side voicing filter predicate so it mirrors the model-level filter behavior for `Recommended`, `Starter`, `Full chord`, and `Dominant pockets`.
- Added explicit rendered metadata flags to selector cards, detail cards, and SVG highlights:
  - `data-is-starter`
  - `data-is-full-chord`
- Made the no-match empty state visible on initial render when a selected filter combination has no matches.
- Updated tests to cover default `Recommended`, `Starter`, `Full chord`, grip filtering, combined Full chord + grip filtering, no-match empty state, and the selected detail state.

Intentionally not changed:

- Backend routing.
- `/api/answer` response schema.
- Retrieval gating.
- Chroma/vector stores, embeddings, corpus-private, corpus-v2, source-inbox, scraping.
- Deployment, DNS, auth/security.
- Fret formula, string math, visual assets, decorative SVG.

## Files Changed

- `ui/pedal-steel-fretboard.js`
- `tests/test_pedal_steel_fretboard_ui.py`
- `docs/handoffs/task-completions/answer-ui-fretboard-filter-visibility-fix.md`

No files were deleted. No generated artifacts were intentionally created.

## Exact QA Blocker Addressed

Browser QA blocker:

- Default `Recommended` rendered `0 / 44` cards for `How do I play a G chord on the E9?`
- `Starter` rendered `0` cards.
- `Full chord` rendered `0` cards.
- `Full chord + 4-5-6` rendered `0` cards even when matching full-chord 4-5-6 positions should exist.

The patch targets that browser interaction path, not answer generation.

## Root Cause

The model-level predicate handled semantic filter values:

- `recommended`
- `starter`
- `full-chord`
- `dominant`
- direct voicing categories such as `root-position`, `inversions`, `partial-rootless`

The browser/DOM interaction predicate only handled `all` specially, then compared:

```js
data-voicing-category === selectedFilter
```

That meant filters like `recommended`, `starter`, and `full-chord` could never match DOM elements unless those exact values were in `data-voicing-category`. They were not. Most card categories were values like `root-position`, `inversions`, or `partial-rootless`.

## Filter Predicate Fix

The DOM predicate now evaluates:

- `recommended` via `data-visible-by-default="true"`
- `starter` via `data-is-starter="true"`
- `full-chord` via `data-is-full-chord="true"`
- `dominant` via `data-is-dominant="true"`
- category filters via `data-voicing-category`
- `all` as unconstrained

Rendered selector cards, detail cards, and SVG highlights now carry the same semantic flags so the browser path can make the same decision for every rendered position surface.

## Selected Detail State Fix

The existing selected-detail reset path remains in place:

- After every filter change, `updatePositionFilter()` computes visibility for selector cards, detail cards, and SVG highlights.
- It finds the first visible selector card.
- If one exists, it calls `selectPosition(...)` for that visible card.
- If none exists, it clears `data-selected-position-id` and shows the no-match empty state.

The new predicate makes that path work for `Recommended`, `Starter`, and `Full chord`.

## Default Visible Card Behavior

Default behavior remains conservative:

- `Recommended` is selected by default when the payload supports useful filters.
- Recommended means `visibleByDefault !== false`.
- The prior cap behavior remains: large recommended sets can still be limited so the page does not dump every card.

## Combined Filter Behavior

Combined filtering now works because both predicates are applied to the same rendered elements:

- voicing predicate: `positionElementMatchesVoicing(...)`
- grip predicate: `positionElementMatchesGrip(...)`

Tests now cover:

- Full chord + `4-5-6` shows matching cards.
- Root position + `3-4-5` with no matching card shows the empty state.
- Grip-filtered cards, details, and highlights stay aligned.

## No-Match Empty State Behavior

No-match filter combinations now show:

```text
No positions match these filters. Try All positions or a different grip.
```

The empty state is visible on initial render when a requested filter combination has no matches, and remains managed by `updatePositionFilter()` during browser interactions.

## Tests And Checks

Passed:

```bash
git status --short
git diff --check
node --check ui/answer-client.js
node --check ui/pedal-steel-fretboard.js
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py -q
.venv/bin/python -m pytest tests/test_same_origin_smoke_server.py -q
.venv/bin/python -m pytest
```

Results:

- Focused frontend/fretboard tests: `49 passed`
- Focused API/search/full-answer-quality tests: `238 passed`
- Same-origin smoke server tests: `9 passed`
- Full suite: `668 passed`
- Whitespace check: passed

## Screenshots

No new screenshots were captured in this Lane 06 patch.

The preceding QA handoff includes transient screenshot paths under `/tmp/steel_guitar_rag-answer-ui-fretboard-filter-smoke/` that demonstrated the failure. A fresh Lane 15 browser smoke should capture the fixed state.

## Risks

Risk: Medium.

Why:

- Automated tests now cover the exact root cause, and full pytest is green.
- This still needs browser confirmation because the original blocker appeared in browser interaction after render/bind.
- Worktree remains broadly dirty across unrelated lanes, so any eventual commit must be exact-path staged.

Rollback:

- Revert this patch in `ui/pedal-steel-fretboard.js` and the corresponding new assertions in `tests/test_pedal_steel_fretboard_ui.py`.

## Exact Next QA Prompt

Lane `15 QA / Answer Eval`:

```text
Run protected-preview or local current-worktree browser smoke for the fretboard filter visibility fix on branch feature/answer-api.

Do not deploy, commit, change DNS, touch Chroma, regenerate embeddings, run scraping, or modify files.

Test:
- How do I play a G chord on the E9?
- Where do I play a G chord on the E9?
- How do I play an A chord?
- How do I play a D chord?
- How do I play a D chord across the fretboard of the E9?
- Show me the fretboard
- What’s it mean for a song to be a swing or a waltz?

Verify:
- default Recommended view shows visible cards/details, not 0 cards
- Recommended shows recommended/starter cards when available
- Starter shows visible starter cards when available
- Full chord shows visible full-chord cards when available
- Full chord + grip 4-5-6 shows matching cards when they exist
- grip filters still filter selector cards, detail cards, and SVG highlights together
- no-match combinations show “No positions match these filters. Try All positions or a different grip.”
- selected detail updates to a visible card after filtering
- All positions still reveals the full card set
- non-fretboard prompts show no fretboard
- no [object Object]
- no weak-source warning as primary answer
- no raw forum/source fragment as primary answer
```

## Integration Notes

- UI-only patch.
- No API/schema/backend/retrieval/corpus/deployment changes.
- Safe-to-stage files for this patch after QA approval:
  - `ui/pedal-steel-fretboard.js`
  - `tests/test_pedal_steel_fretboard_ui.py`
  - `docs/handoffs/task-completions/answer-ui-fretboard-filter-visibility-fix.md`
- Keep unrelated dirty files unstaged, including backend, corpus, source-inbox, deployment, generated data, visual assets, and prior parked UI/landing work unless explicitly approved.

## Suggested Next Step

Recommended lane: `15 QA / Answer Eval`.

Rerun the browser smoke above. If it passes, return to `01 Repo Steward` for exact-path commit preparation.
