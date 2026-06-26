# E9 Explorer Path Mode String-Group Visibility

## Task Summary

Lane: 06 UX/UI Design

Requested: fix the E9 Fretboard Explorer controls so the exact `String group` selector is hidden/removed when `Explore mode` is `Harmonized scale path`.

Completed:

- Reproduced the defect locally: JS set `hidden=true`, but CSS `.explorer-control { display: grid; }` still made the control visually render.
- Added an explicit `[hidden] { display: none !important; }` rule so hidden Explorer controls are actually removed from layout.
- Disabled and ARIA-hid the exact string-group selector in path mode.
- Disabled and ARIA-hid the path-family selector outside path mode.
- Preserved existing path-row logic: path mode ignores prior exact string-group selections and displays mixed path groups.
- Refreshed the Explorer script query so browser/protected-preview pages fetch the updated behavior.

Intentionally not changed:

- Backend Explorer data/model generation.
- Fretboard geometry, notation mapping, marker labels, copedent data, or source/RAG behavior.
- Corpus, Chroma, embeddings, scraping, auth, DNS, deployment config, private source data, or visual assets.

## Files Changed

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-26-1402-06-explorer-path-string-group-visibility.md`
- `docs/handoffs/task-completions/assets/2026-06-26-path-string-group-visibility/local-path-mode-controls.png`

## Root Cause

The Explorer JS already set `explorer-string-group-control.hidden = true` in path mode, and `getBaseRows()` already returned `pathRows(matchingRows)` before applying exact string-group filtering.

The visible defect came from CSS: `.explorer-control { display: grid; }` overrode the browser's default hidden-element display behavior, so the wrapper still rendered even with the `hidden` attribute present.

## Behavior Changed

Single grip mode:

- `String group` selector is visible.
- Exact string-group filtering continues to work.
- `Path family` selector is hidden and disabled.

Harmonized scale path mode:

- `String group` selector is visually hidden, disabled, and `aria-hidden="true"`.
- `Path family` selector is visible, enabled, and `aria-hidden="false"`.
- Prior exact string-group selection no longer appears to be an active path control.
- Low path continues to show mixed groups: `6-8-10, 6-7-10, 6-7-10, 6-8-10, 6-8-10, 6-7-10, 6-8-10, 6-8-10`.

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

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=path-string-group-visibility-fix-local`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=path-string-group-visibility-fix-local`
- Exact URL the user should use: protected-preview URL after commit/protected smoke
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `9b2b3b8` plus local scoped changes
- Version endpoint: not checked for local static browser smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local working tree and browser URL cache-bust
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: not relevant to direct Explorer smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not relevant to direct Explorer smoke
- Who should test this URL: Codex locally, then the user after protected-preview smoke
- Do not test these URLs: uncache-busted Explorer URLs for this fix
- Known caveats: local browser smoke does not prove protected-preview static asset freshness

Local smoke result:

- Page loaded.
- Single grip mode showed `String group`.
- Single grip mode filtered cards to `6-8-10`.
- Harmonized scale path mode hid `String group` visually.
- Harmonized scale path mode showed `Path family`.
- Harmonized scale path mode disabled the hidden string-group selector.
- Low path showed both `6-8-10` and `6-7-10` cards/markers.
- Switching back to Single grip restored the `String group` selector.
- No `[object Object]`.
- No relevant console errors.

Screenshot:

- `docs/handoffs/task-completions/assets/2026-06-26-path-string-group-visibility/local-path-mode-controls.png`

## Integration Notes

- The data/model path behavior was already correct; the user-facing bug was CSS visibility plus semantic enabled state.
- `ui/e9-fretboard-explorer.html` now references `e9-fretboard-explorer.js?v=path-string-group-visibility-20260626`.
- Protected-preview smoke should use a fresh direct Explorer cache-busted URL after commit.

## Risk Assessment

Risk: low.

Reason: the CSS rule restores standard hidden-element behavior, and JS changes only disable/ARIA-hide controls already hidden by mode.

Rollback: revert the `[hidden]` CSS rule, `syncExploreModeControls()` disabled/ARIA updates, and corresponding tests.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-26-1402-06-explorer-path-string-group-visibility.md`
- `docs/handoffs/task-completions/assets/2026-06-26-path-string-group-visibility/local-path-mode-controls.png`

## Files That Must Not Be Staged

- Existing unrelated dirty files listed by `git status --short`, especially corpus/source/private/design/deployment-adjacent files.
- `docs/handoffs/task-completions/integration-status.md` until protected-preview smoke is recorded.

## Recommended Next Lane

Lane 01 exact-path commit, then Lane 12 protected-preview smoke for the direct Explorer page.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Commit scoped files with:

```bash
git add ui/e9-fretboard-explorer.html ui/e9-fretboard-explorer.js tests/test_frontend_answer_ui.py docs/handoffs/task-completions/2026-06-26-1402-06-explorer-path-string-group-visibility.md docs/handoffs/task-completions/assets/2026-06-26-path-string-group-visibility/local-path-mode-controls.png
git commit -m "fix: hide string group selector in path mode"
```
