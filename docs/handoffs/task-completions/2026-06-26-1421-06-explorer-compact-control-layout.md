# E9 Explorer Compact Control Layout

## Task Summary

Lane: 06 UX/UI Design

Requested: clean up the E9 Fretboard Explorer top controls so `String group` does not consume a full-width listbox row, `Notation` is clearly labeled, and the useless `Showing validated positions` status text is removed.

Completed:

- Changed the Explorer control grid from fixed five-column layout to responsive `auto-fit` columns.
- Changed `String group` from a full-width multi-select listbox to a compact normal select/dropdown.
- Moved the four-way notation selector into the main controls area with a visible `Notation` label.
- Removed the visible `Showing validated positions` status pill.
- Preserved single-grip string-group filtering.
- Preserved path-mode behavior: `String group` hides/disables and `Path family` shows/enables.
- Refreshed the Explorer script query to `e9-fretboard-explorer.js?v=compact-controls-20260626`.

Intentionally not changed:

- Backend Explorer data or validation.
- Fretboard geometry, marker labeling, notation logic, copedent data, or harmonized path data.
- Corpus, Chroma/vector stores, embeddings, scraping, auth, DNS, deployment config, source cards, or private source data.

## Files Changed

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-26-1421-06-explorer-compact-control-layout.md`
- `docs/handoffs/task-completions/assets/2026-06-26-compact-explorer-controls/local-desktop-controls.png`
- `docs/handoffs/task-completions/assets/2026-06-26-compact-explorer-controls/local-mobile-controls.png`

## Behavior Changed

Single grip mode:

- `String group` is visible as a compact dropdown.
- Selecting `6-8-10` filters cards/markers to `6-8-10`.
- `Path family` is hidden and disabled.

Harmonized scale path mode:

- `String group` is hidden and disabled.
- `Path family` is visible and enabled.
- Low path continues to render mixed string groups `6-8-10` and `6-7-10`.

Control layout:

- `String group` no longer spans the full grid or renders as a tall listbox.
- `Notation` sits in the top control grid with a visible label.
- The scale notes pill remains; the validation-status pill was removed.

## Tests And Checks

Commands run:

```bash
node --check ui/e9-fretboard-explorer.js
node --check ui/e9-fretboard-explorer-data.js
node --check ui/answer-client.js
node --check ui/pedal-steel-fretboard.js
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
git diff --check
```

Results:

- `node --check ui/e9-fretboard-explorer.js`: passed
- `node --check ui/e9-fretboard-explorer-data.js`: passed
- `node --check ui/answer-client.js`: passed
- `node --check ui/pedal-steel-fretboard.js`: passed
- `tests/test_frontend_answer_ui.py`: 23 passed
- `tests/test_fretboard_explorer.py`: 38 passed
- `tests/test_pedal_steel_fretboard_ui.py`: 34 passed
- `git diff --check`: passed

## Browser Smoke

Smoke Target:

```text
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=compact-controls-local
- Cache-busted URL tested: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=compact-controls-local
- Exact URL the user should use: protected-preview URL after commit/protected smoke
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: 5b9ba1f plus scoped local changes
- Version endpoint: not checked for local static browser smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local working tree and browser URL cache-bust
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: not relevant to direct Explorer smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not relevant to direct Explorer smoke
- Who should test this URL: Codex locally, then the user after protected-preview smoke
- Do not test these URLs: uncache-busted Explorer URLs for this slice
- Known caveats: local browser smoke does not prove protected-preview static asset freshness
```

Local desktop smoke result:

- Page loaded.
- Explorer loaded `e9-fretboard-explorer.js?v=compact-controls-20260626`.
- `String group` rendered as a compact dropdown, not a multi-select listbox.
- `String group` control width was about 186px inside a roughly 998px control grid.
- `Notation` label was visible.
- `Showing validated positions` was absent.
- Selecting `6-8-10` filtered rows to `6-8-10`.
- Harmonized scale path hid `String group`, showed `Path family`, and kept mixed low-path groups `6-8-10` and `6-7-10`.
- No `[object Object]`.
- No relevant browser console warnings/errors.

Local narrow smoke result:

- URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=compact-controls-local-mobile`
- Controls wrapped without page-level horizontal overflow.
- `String group` stayed usable.
- `Notation` label remained visible.
- `Showing validated positions` stayed absent.

Screenshots:

- `docs/handoffs/task-completions/assets/2026-06-26-compact-explorer-controls/local-desktop-controls.png`
- `docs/handoffs/task-completions/assets/2026-06-26-compact-explorer-controls/local-mobile-controls.png`

## Integration Notes

- The UI now exposes only one string group at a time from the compact dropdown. The underlying renderer still handles selected option state and preserves `All` or exact group filtering.
- The path mode fix from `7b934e6` remains intact.
- Protected-preview smoke should use a fresh direct Explorer cache-busted URL after commit.

## Risk Assessment

Risk: low to medium.

Reason: layout and markup changed in the top controls, but core Explorer data, filters, notation, and fretboard rendering logic are preserved and covered by focused tests plus local browser smoke.

Rollback: revert the compact-control HTML/CSS changes, the result-count guard, and matching tests.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-26-1421-06-explorer-compact-control-layout.md`
- `docs/handoffs/task-completions/assets/2026-06-26-compact-explorer-controls/local-desktop-controls.png`
- `docs/handoffs/task-completions/assets/2026-06-26-compact-explorer-controls/local-mobile-controls.png`

## Files That Must Not Be Staged

- Existing unrelated dirty files listed by `git status --short`, especially corpus/source/private/design/deployment-adjacent files.
- `docs/handoffs/task-completions/integration-status.md` until protected-preview smoke is recorded.

## Recommended Next Lane

Lane 01 exact-path commit, then Lane 12/protected-preview browser smoke for the direct Explorer page.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Commit scoped files with:

```bash
git add ui/e9-fretboard-explorer.html ui/e9-fretboard-explorer.js tests/test_frontend_answer_ui.py docs/handoffs/task-completions/2026-06-26-1421-06-explorer-compact-control-layout.md docs/handoffs/task-completions/assets/2026-06-26-compact-explorer-controls/local-desktop-controls.png docs/handoffs/task-completions/assets/2026-06-26-compact-explorer-controls/local-mobile-controls.png
git commit -m "fix: compact explorer control layout"
```
