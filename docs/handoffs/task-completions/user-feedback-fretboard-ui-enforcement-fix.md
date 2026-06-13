# User Feedback Fretboard UI Enforcement Fix

## Task Summary

Branch: `feature/answer-api`
HEAD: `97071e6`

Requested: enforce the user feedback that the smoke-ready answer UI still had not fully reflected:

- Make "Why these families matter" use available answer-page width instead of creating a narrow, vertical section.
- Ensure grip filters filter the visible fretboard highlights, selector cards, and detail/card list below the fretboard.
- Keep the default learner detail view focused on useful playing information and move internal metadata behind "Technical details."
- Keep learner-friendly voicing filters present.
- Keep the default view limited and nonempty, with "All positions" as an explicit opt-in.

Completed in this pass:

- Renamed the voicing filter's all-state label from `All` to `All positions` in `ui/pedal-steel-fretboard.js`.
- Added focused assertions in `tests/test_pedal_steel_fretboard_ui.py` so the learner-facing `All positions` voicing control remains present.
- Verified the existing implementation already filters selectors, detail panels, and SVG highlights through the same voicing/grip predicate.
- Verified the existing implementation already hides empty learner fields and collapses internal metadata under `Technical details`.
- Verified the existing answer-page implementation already marks "Why these families matter" as a wide answer section.

Intentionally not changed:

- No backend routing, answer schema, retrieval gating, corpus, Chroma, embeddings, scraping, auth, deployment, DNS, public assets, or raw design assets were changed.
- No broad copy/product rename was performed.
- No staging or commit was performed.

## Files Changed

Changed by this pass:

- `ui/pedal-steel-fretboard.js`
- `tests/test_pedal_steel_fretboard_ui.py`
- `docs/handoffs/task-completions/user-feedback-fretboard-ui-enforcement-fix.md`

Already dirty before this pass and intentionally left alone:

- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- Many cross-lane backend, corpus, deployment, and docs files shown by `git status --short`.

Deleted files: none.
Generated artifacts: none.

## User Feedback Coverage

1. "Why these families matter" too narrow:

- Existing UI code already routes this section through `shouldUseWideAnswerSection(section)` and applies `.answer-section.is-wide`.
- Existing CSS spans wide sections across the answer grid with `grid-column: 1 / -1`.
- Existing frontend tests assert the wide-section behavior.
- No new layout patch was needed in this pass.

2. Grip filtering must filter the card/detail list:

- Existing `updatePositionFilter()` applies the same visibility result to `[data-position-selector]`, `[data-position-detail]`, and `.pedal-steel-fretboard__highlight`.
- Existing tests cover grip `3-4-5`, grip `4-5-6`, combined voicing + grip, and no-match behavior.
- No new predicate patch was needed in this pass.

3. Learner view should not expose internal metadata by default:

- Existing `renderPositionDetail()` shows learner fields first: Fret, Grip, Pedals, Levers, Notes, Intervals, When to use, and Short explanation.
- Existing `renderTechnicalDetails()` moves internal fields behind a collapsed `Technical details` section.
- Existing `isEmptyLearnerValue()` hides empty values such as `none`, `not found`, `not specified`, `not yet linked`, and `unknown`.
- No new metadata patch was needed in this pass.

4. Voicing filters must be present:

- Existing voicing controls include Recommended, Starter, Full chord, Root position, Inversions, Partial/rootless, Dominant pockets, and an all-state.
- This pass changed the all-state label to `All positions` to match the requested learner-facing language.

5. Default should not show all cards:

- Existing model defaults to `recommended`.
- Existing recommended cap limits the default visible set to `MAX_RECOMMENDED_VISIBLE_POSITIONS = 5`.
- Existing tests cover default nonempty recommended/starter/full-chord behavior and `All positions` reveal behavior.

## Before / After Behavior

Before:

- The voicing all-state appeared as `All`, while the rest of the requested UI language used `All positions`.
- This made the filter system feel less explicit for a learner and left a small mismatch with the user feedback.

After:

- The voicing all-state button now reads `All positions`.
- The separate recommended-cap reveal button still reads `All positions`.
- Existing default recommended behavior, grip filtering, voicing filtering, combined filters, no-match empty state, and learner/technical detail split remain unchanged.

## Filter Behavior

Current behavior verified through tests/source inspection:

- Recommended is selected by default and limits visible positions.
- Starter filters to starter positions.
- Full chord filters to positions with full chord metadata.
- Root position, Inversions, Partial/rootless, and Dominant pockets filter by voicing category or derived metadata.
- Grip controls filter to the selected grip.
- Combined voicing + grip filters are composed.
- Empty combinations show: `No positions match these filters. Try All positions or a different grip.`
- Selected detail resets to the first visible selector after filters change.

## Default Card Count Behavior

- Default view uses the recommended filter.
- Recommended extra positions are hidden when the recommended cap applies.
- The cap is currently `5`.
- `All positions` is opt-in through the voicing all-state and the recommended-cap reveal button.

## Learner Fields vs Technical Fields

Learner-visible detail fields:

- Fret
- Grip
- Pedals
- Levers
- Notes
- Intervals
- When to use
- Short explanation

Collapsed under `Technical details`:

- Validation status
- Family
- Tier
- Role
- Position kind
- Why classified
- Forum usage evidence
- Omitted intervals
- Movement use
- Resolution use
- Extended explanation
- Caveats
- Voicing
- Sound character
- What is omitted

Empty values such as `none` and `not_found` are hidden by default when rendered through the detail helpers.

## Screenshots

No new screenshots were captured in this pass. The latest relevant browser QA evidence is in:

- `docs/handoffs/task-completions/qa-answer-ui-fretboard-filter-visibility-fix.md`

## Tests and Checks

Commands run:

```bash
git status --short
node --check ui/answer-client.js
node --check ui/pedal-steel-fretboard.js
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py tests/test_frontend_answer_ui.py -q
git diff --check
```

Results:

- `node --check ui/answer-client.js`: passed
- `node --check ui/pedal-steel-fretboard.js`: passed
- Focused UI tests: `49 passed`
- `git diff --check`: passed

Skipped:

- Browser smoke was not rerun in this pass. The code change is a label/test assertion only; Lane 15 should still run the next answer-page/fretboard smoke before commit if visual confidence is required.
- API tests were not run because no backend, contract, routing, or retrieval code was modified by this pass.

## Integration Notes

- This is a narrow Lane 06 UX/UI change.
- It does not change the `/api/answer` schema or fretboard payload contract.
- It does not change fretboard math, string math, position filtering predicates, or selected-card state logic.
- It reinforces that the learner-facing all-state is named `All positions`.

Exact safe-to-stage file list for this pass:

- `ui/pedal-steel-fretboard.js`
- `tests/test_pedal_steel_fretboard_ui.py`
- `docs/handoffs/task-completions/user-feedback-fretboard-ui-enforcement-fix.md`

Files that must remain unstaged unless separately approved:

- Backend/RAG files
- Corpus/private/source-inbox/provenance files
- Deployment/DNS/Cloudflare files
- `public/`, `ui/brand/`, `Neon Sign/`, and raw design assets
- Existing unrelated dirty files shown by `git status --short`

## Risk Assessment

Risk: low.

Why:

- The implementation patch changes one UI label and associated tests.
- Existing filter behavior and answer layout mechanics were not altered.
- Syntax and focused UI tests passed.

Rollback:

- Revert the one-line label change in `ui/pedal-steel-fretboard.js` and the matching test assertions.

## Commit Readiness

Needs human review first.

Reason:

- The focused checks are green, but the broader worktree has many unrelated dirty files across lanes.
- Lane 15 should decide whether to rerun browser smoke after this label alignment before Repo Steward stages exact paths.

## Suggested Next Step

Recommended lane: `15 QA / Answer Eval`

Exact next QA prompt:

```text
Lane 15 QA: Browser-smoke the answer-page fretboard UI after the user-feedback enforcement fix. Verify "Why these families matter" uses full width, Recommended default shows useful cards, voicing filters include "All positions", grip filters filter both SVG/cards and detail list, combined filters work, no-match state is clear, technical details are collapsed, non-fretboard prompts show no fretboard, and no [object Object] appears. Do not modify files; write a QA handoff with pass/fail table and screenshots if possible.
```
