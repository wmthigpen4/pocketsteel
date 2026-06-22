# E9 Fretboard Explorer User-Smoke UI Fixes

## Task Summary

Lane: 06 UX/UI Design

Requested: fix user-smoke issues on the E9 Fretboard Explorer after protected-preview smoke passed technically but exposed usability failures.

Completed:
- Made the string-group selector mode-aware.
- Disabled unavailable harmony modes for the selected scale.
- Prevented stale invalid string-group values from making the fretboard appear blank.
- Suppressed dense SVG text labels on the Explorer fretboard while preserving marker dots/bands and full row cards/details.
- Added focused regression coverage for the Explorer controller and the shared fretboard label-density option.

Intentionally not changed:
- No backend, payload generation, corpus, Chroma, embeddings, scraper output, deployment, auth, DNS, assets, or private source data changes.
- No changes to deterministic Explorer rows.
- No changes to canonical pitch validation.

## Files Changed

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `ui/pedal-steel-fretboard.js`
- `tests/test_frontend_answer_ui.py`
- `tests/test_pedal_steel_fretboard_ui.py`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-user-smoke-ui-fixes.md`

Generated artifacts:
- None.

Deleted files:
- None.

## What Changed

### Mode-Aware Filter Behavior

- `2-string harmonized scale` now rebuilds the string-group selector to show only validated 2-string groups:
  - `All 2-string groups`
  - `3-5`
  - `5-6`
  - `6-10`
  - `4-6`
  - `3-4`
- `3-string diatonic harmony` now rebuilds the string-group selector to show only validated 3-string groups:
  - Core grips: `3-4-5`, `4-5-6`, `5-6-8`, `6-8-10`
  - Advanced swaps: `5-6-7`, `6-7-10`, `5-7-8` when available
- Stale invalid string-group selections are reset to `all`.

### Empty-State / Disabled-State Behavior

- If a selected scale has no rows for a harmony mode, that harmony mode is disabled.
- Current payload state:
  - G major supports 2-string harmonized scale and 3-string diatonic harmony.
  - G natural minor supports 3-string diatonic harmony.
  - G natural minor disables 2-string harmonized scale and switches to valid 3-string rows instead of silently showing a blank fretboard.
- If future data creates a true no-match state, the page displays a clear empty message naming the unavailable mode and scale.

### Fretboard Label-Density Fix

- Added `showHighlightLabels: false` support to `ui/pedal-steel-fretboard.js`.
- The Explorer passes `showHighlightLabels: false`, so full row labels no longer stack over the fretboard.
- Marker dots/bands remain visible.
- Full learner-facing text remains in the row card/detail area:
  - `display_notes`
  - `display_top_voice`
  - `display_summary`
  - fret
  - string group
  - pedals/levers
  - per-string changes
  - warnings
  - pitch validation status

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8896/ui/e9-fretboard-explorer.html?v=e9-explorer-user-smoke-fixes-local`
- Cache-busted URL tested: `http://127.0.0.1:8896/ui/e9-fretboard-explorer.html?v=e9-explorer-user-smoke-fixes-local`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-user-smoke-fixes-20260622`
- Auth required: yes for protected preview
- Auth provider: Cloudflare Access for protected preview
- Cloudflare Access login result: not attempted in this local smoke
- Local backend URL: not used
- Expected backend port: not used
- Expected git HEAD: `5fb23e2` before this fix commit
- Version endpoint: not used
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: local working tree and git HEAD
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not relevant for this surface
- Whether `/ui/e9-fretboard-explorer.html` works: yes locally
- Whether `/ui/e9-fretboard-explorer.html` is expected to work: yes
- Who should test this URL: Lane 15 and the user after protected preview includes the commit
- Do not test these URLs: public/www landing URLs for this task
- Known caveats: the plain local static server did not map `/brand`, so it logged 404s for `/brand/pedal-steel-fretboard-background.svg`; protected preview is expected to serve `/brand` normally.

## Browser Smoke Results

Local in-app browser smoke:

- Initial 3-string mode:
  - Group options: `All 3-string groups`, core grips, advanced swaps.
  - Result count: 34 validated rows.
  - Highlight dots: present.
  - SVG text labels: 0.
  - `[object Object]`: not present.
- Switched to 2-string harmonized scale:
  - Group options rebuilt to `All 2-string groups`, `3-5`, `5-6`, `6-10`, `4-6`, `3-4`.
  - Stale `4-5-6` selection reset to `all`.
  - Result count: 40 validated rows.
  - Empty state not shown.
  - SVG text labels: 0.
- Switched to G natural minor from 2-string mode:
  - `two_string_harmonized` disabled.
  - Harmony switched to `three_string_diatonic`.
  - Group options rebuilt to valid 3-string groups.
  - Scale notes rendered `G A Bb C D Eb F`.
  - Result count: 32 validated rows.
  - Empty state not shown.
  - `[object Object]`: not present.
- Narrow viewport, 390 x 844:
  - Controls collapsed to one column.
  - No page-level horizontal overflow.
  - Highlight dots remain visible.
  - SVG text labels remain suppressed.

Browser logs:
- No console warnings/errors from the Explorer UI.

## Tests And Checks

Commands run:

```bash
git status --short
git branch --show-current
node --check ui/e9-fretboard-explorer.js
node --check ui/e9-fretboard-explorer-data.js
node --check ui/pedal-steel-fretboard.js
node --check ui/answer-client.js
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
.venv/bin/python -m pytest -q
git diff --check
```

Results:
- JS syntax checks: passed.
- `tests/test_pedal_steel_fretboard_ui.py`: 31 passed.
- `tests/test_frontend_answer_ui.py`: 23 passed.
- `tests/test_fretboard_explorer.py`: 11 passed.
- Full pytest: 791 passed.
- `git diff --check`: passed.

## Integration Notes

- The fix is UI-only.
- The Explorer surface still uses the existing validated static browser fixture.
- The shared fretboard renderer keeps default SVG label behavior unless callers pass `showHighlightLabels: false`.
- Lane 15 should rerun protected-preview browser smoke on the cache-busted URL after this commit is available in the protected preview runtime.

## Risk Assessment

Risk: Low to medium.

Why:
- Low backend/data risk: no backend or payload changes.
- Medium UI risk: protected-preview browser smoke is still needed against the deployed/protected runtime.

Rollback notes:
- Revert this commit or remove the `showHighlightLabels` option use and the Explorer controller option-rebuilding logic.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `ui/pedal-steel-fretboard.js`
- `tests/test_frontend_answer_ui.py`
- `tests/test_pedal_steel_fretboard_ui.py`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-user-smoke-ui-fixes.md`

## Files That Must Not Be Staged

Do not stage unrelated dirty or untracked files shown by `git status --short`, especially:
- Corpus/private/source-inbox/provenance files.
- Chroma/vector/embedding outputs.
- Deployment/DNS/auth/secrets files.
- Visual/raw asset directories such as `public/`, `ui/brand/`, and `Neon Sign/`.
- Existing unrelated modified docs/scripts/reports.

## Recommended Next Lane

Lane 15 QA / Answer Eval.

Suggested prompt:

```text
Lane 15: Browser-smoke the E9 Fretboard Explorer user-smoke fixes at https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-user-smoke-fixes-20260622. Verify mode-aware string-group options, natural-minor harmony disable/switch behavior, no blank stale-filter state, no overlapping SVG text labels, full row details in cards, no [object Object], and no regressions to G natural minor Bb/Eb spelling.
```

## Commit Readiness

Safe to commit.

## Suggested Next Step

Commit this scoped Explorer UI fix, then ask Lane 15 to smoke the protected-preview URL above.
