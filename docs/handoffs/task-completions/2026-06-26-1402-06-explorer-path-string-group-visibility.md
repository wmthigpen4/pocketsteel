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
- `docs/handoffs/task-completions/assets/2026-06-26-path-string-group-visibility/protected-path-mode-controls.png`

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

Protected-preview smoke result:

- Commit tested: `7b934e6`.
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=path-string-group-visibility-7b934e6`.
- Cloudflare Access result: succeeded from the existing authenticated in-app browser session; the Explorer page loaded directly.
- Explorer HTML loaded `e9-fretboard-explorer.js?v=path-string-group-visibility-20260626`.
- Single grip mode with `6-8-10` selected showed the `String group` selector and filtered rows to `6-8-10`.
- Harmonized scale path mode hid the `String group` selector visually, disabled it, and showed the `Path family` selector.
- Low path rows included mixed groups `6-8-10` and `6-7-10`, proving the prior exact string-group value did not silently filter the path.
- Switching back to Single grip restored the `String group` selector.
- No `[object Object]` appeared.
- No relevant console errors were observed during the local browser smoke; the protected smoke used DOM-state checks.

Protected Smoke Target:

```text
- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=path-string-group-visibility-7b934e6
- Cache-busted URL tested: https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=path-string-group-visibility-7b934e6
- Exact URL the user should use: https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=path-string-group-visibility-7b934e6
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded from existing browser session
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: 7b934e6
- Version endpoint: http://127.0.0.1:8770/api/version
- Version endpoint result: git_sha=4040a47; server process was not restarted for this static UI fix
- If version endpoint missing, how version is inferred: protected HTML script query and cache-busted URL verified the current static UI path
- Whether app root `/` works: local root returns 302 to /ui/steel-guitar-rag-mock.html
- Whether app root `/` is expected to work: yes, with redirect
- Whether `/ui/steel-guitar-rag-mock.html` works: local static route available; not the target for this Explorer-only smoke
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: the user
- Do not test these URLs: uncache-busted Explorer URLs for this slice
- Known caveats: /api/version remains on older server-start SHA 4040a47 because no protected-preview restart was performed; this smoke verifies browser-loaded static UI behavior.
```

Protected screenshot:

- `docs/handoffs/task-completions/assets/2026-06-26-path-string-group-visibility/protected-path-mode-controls.png`

## Integration Notes

- The data/model path behavior was already correct; the user-facing bug was CSS visibility plus semantic enabled state.
- `ui/e9-fretboard-explorer.html` now references `e9-fretboard-explorer.js?v=path-string-group-visibility-20260626`.
- Protected-preview smoke passed at `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=path-string-group-visibility-7b934e6`.

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

## Recommended Next Lane

Lane 15/user smoke for the direct Explorer page.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Implementation commit created:

```bash
7b934e6 fix: hide string group selector in path mode
```

Next recommended check: user smoke the protected URL above and verify `String group` is visible in Single grip but absent in Harmonized scale path.
