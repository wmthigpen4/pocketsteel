# Fretboard Position Card Filter User-Smoke Fix

## Task Summary

Autopilot user-smoke bug: the protected-preview fretboard filters appeared to update the fretboard markers, but the learner-facing position cards below the fretboard still showed unrelated cards after selecting grip and control filters.

Completed a scoped `06 UX/UI Design` frontend repair. The fix keeps backend routing, `/api/answer` schema, auth, deployment, corpus, Chroma/vector stores, embeddings, source data, scraping, and visual assets untouched.

## Root Cause

The component already had a filter-sync path for voicing and grip, but pedal/lever controls were not modeled, and the rendered card/detail/highlight elements did not all carry the same control-combination metadata. This made it too easy for card rendering and marker/detail state to drift as the UI gained more filter modes.

## Files Changed

- `ui/pedal-steel-fretboard.js`
  - Added learner-facing Pedals / Levers filter options derived from position data.
  - Added shared pedal/lever filter normalization for labels such as `No pedals/levers`, `A+B`, `A+F`, `E-lower`, `F lever`, `B+C`, and `Vertical` when present.
  - Added `data-position-pedal-lever-key`, `data-position-pedal-lever-label`, and `data-active-pedal-lever-filters` to the rendered DOM.
  - Made voicing, grip, and pedal/lever filters combine into one visible-position set.
  - Applies visibility to position cards, detail panels, SVG highlights, and legend items with both `hidden` and `style.display = "none"` for defensive browser behavior.
  - Clears grip and pedal/lever filters when `All positions` is selected.
  - Updates the empty state to: `No positions match these filters. Try All grips, All pedals/levers, or All positions.`
- `tests/test_pedal_steel_fretboard_ui.py`
  - Added focused coverage for pedal/lever filter option rendering and card/detail/highlight visibility.
  - Added combined voicing + grip + pedal/lever filter coverage.
  - Added multi-select pedal/lever model/render checks.
  - Updated source-level checks for the shared filter-sync path.

## Smoke Target

- Target type: local
- Exact browser URL: `http://127.0.0.1:59817/ui/steel-guitar-rag-mock.html?v=fretboard-card-filter-local`
- Cache-busted URL: `http://127.0.0.1:59817/ui/steel-guitar-rag-mock.html?v=fretboard-card-filter-local`
- Auth required: no
- Auth provider: none
- Local backend URL: not used; isolated local component page
- Expected backend port: not used
- Expected git HEAD: current worktree based on `ab32b3b`
- Version endpoint result: not used
- Root URL status: not used as proof
- API fallback status: not used
- Exact URL the user should test: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=fretboard-position-card-filter-<commit>` after protected-preview restart/version verification

This was local browser smoke, not protected-preview proof.

## Smoke Result

Local browser component smoke passed.

Visible position card counts:

- Default/all state: `5` visible cards.
- Grip `3-4-5`: `2` visible cards, both `3-4-5`.
- Grip `4-5-6`: `2` visible cards, both `4-5-6`.
- Pedals / Levers `A+F`: `1` visible card, `A+F`.
- Pedals / Levers `A+F` plus grip `3-4-5`: `1` visible card matching both filters.
- Root position plus `A+F` plus grip `3-4-5`: `0` visible cards with the required empty state.
- `All positions`: `5` visible cards restored.

Checks also confirmed:

- Selected detail panel moved to a visible filtered card.
- SVG highlights matched the same visible card set.
- Non-fretboard text did not gain a fretboard.
- No `[object Object]` appeared.

Protected-preview smoke still needs Lane 12 verification after this commit or a later commit is served.

## Tests And Checks

- `git status --short`
- `git diff --check`
- `node --check ui/pedal-steel-fretboard.js`
- `node --check ui/answer-client.js`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` -> `29 passed`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py tests/test_frontend_answer_ui.py -q` -> `47 passed`
- Local browser component smoke using the Smoke Target above -> passed

Full pytest was not run because this was a scoped frontend/fretboard UI fix and the relevant frontend/fretboard checks passed.

## Integration Notes

- No `/api/answer` schema change.
- No backend routing change.
- The component now expects modern metadata-rich position payloads to expose the Pedals / Levers filter beside existing Voicing and Grip controls.
- Older focused/demo-style payloads without useful voicing/grip controls still avoid rendering a standalone filter panel.

## Risk Assessment

Risk: medium. The change touches core fretboard card filtering and interaction behavior, but it is isolated to the fretboard component and focused tests cover card/detail/highlight visibility.

Rollback: revert the implementation commit if protected-preview browser smoke finds a regression.

## Commit Readiness

Safe to commit after final cached diff checks pass.

## Suggested Next Step

After commit, Lane 12 should restart or verify the protected-preview runtime and smoke the canonical UI path:

`https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=fretboard-position-card-filter-<commit>`

Verify `How do I play a G chord on the E9?`, then select grip `3-4-5`, grip `4-5-6`, Pedals / Levers `A+F`, combined grip plus pedal/lever filters, no-match empty state, and `All positions`.
