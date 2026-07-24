# 2026-06-22 E9 Fretboard Explorer Expanded-Key Preview Refresh

## Task Summary

Lane 12 refreshed the protected-preview static asset cache-busts for the E9 Fretboard Explorer expanded-key UI. The Explorer route now references the slice-specific cache-bust `e9-explorer-expanded-keys-20260622` for:

- `pedal-steel-fretboard.js`
- `e9-fretboard-explorer-data.js`
- `e9-fretboard-explorer.js`

The protected-preview process was restarted with the documented private-preview command. No product logic, corpus data, Chroma/vector stores, embeddings, scraper output, auth policy, DNS, deployment config, private source data, or brand assets were changed.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-expanded-keys-20260622`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-expanded-keys-20260622`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-expanded-keys-20260622`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; authenticated browser loaded the Explorer page, not the Access login page
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `d4b26ad` or later containing the expanded-key Explorer UI
- Version endpoint: `/api/version`
- Version endpoint result: `{"git_sha":"d4b26ad","git_branch":"feature/answer-api","python_module":"steel_guitar_rag.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}`
- Whether app root `/` works: not tested for this task
- Whether app root `/` is expected to work: not required for this Explorer route smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested for this task
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes, but outside this task's scope
- Who should test this URL: Lane 15 and the user
- Do not test these URLs: uncached Explorer URLs for this slice unless diagnosing cache behavior
- Known caveats: direct SVG-tab console emitted one browser-runtime promise error after the raw SVG loaded; the Explorer page itself had no console errors.

## Files Changed

- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-expanded-key-preview-refresh.md`

No files were deleted. No generated artifacts were created.

## Cache-Bust Result

Pass. `rg "e9-explorer-" ui/e9-fretboard-explorer.html` and the served HTML from `127.0.0.1:8770` both show:

```html
<script src="pedal-steel-fretboard.js?v=e9-explorer-expanded-keys-20260622"></script>
<script src="e9-fretboard-explorer-data.js?v=e9-explorer-expanded-keys-20260622"></script>
<script src="e9-fretboard-explorer.js?v=e9-explorer-expanded-keys-20260622"></script>
```

The existing frontend assertion was updated to pin this cache-bust value.

## Protected-Preview Refresh Result

Pass. The private-preview process was restarted in a detached `screen` session:

- Session: `steel-rag-private-preview`
- Listener: `127.0.0.1:8770`
- Process module: `steel_guitar_rag.api`
- Auth provider: `cloudflare_access`
- Retrieval mode: `hybrid_private_first`

## Asset Routing Result

Pass with caveat.

- Local route check: `http://127.0.0.1:8770/brand/pedal-steel-fretboard-background.svg` returned `HTTP/1.0 200 OK` with `Content-Type: image/svg+xml; charset=utf-8`.
- Authenticated protected-preview browser check: `https://app.steelguitarrag.com/brand/pedal-steel-fretboard-background.svg?v=e9-explorer-expanded-keys-20260622` loaded an SVG element and did not show Cloudflare Access login.
- Caveat: the direct raw SVG browser tab logged one `TypeError: Cannot use 'in' operator to search for 'animation' in undefined`. The Explorer page itself had no console errors, so this does not currently block Lane 15 Explorer smoke.

## Quick Browser Checks

Pass.

- Page identifies as `E9 Fretboard Explorer`.
- Expanded key selector includes `G`, `C`, `D`, `F`, `Bb`, and `Eb`.
- Default `G` rows display.
- Selecting `C` changes the displayed rows and scale to `C D E F G A B`.
- `Showing validated positions` appears.
- `validated rows` does not appear in primary copy.
- `E-lower+E-lower` does not appear.
- `[object Object]` does not appear.
- Explorer page console errors: none.
- Page scripts load with `e9-explorer-expanded-keys-20260622`.

## Tests And Checks Run

- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `rg "e9-explorer-" ui/e9-fretboard-explorer.html tests/test_frontend_answer_ui.py`
- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/e9-fretboard-explorer-data.js`
- `node --check ui/pedal-steel-fretboard.js`
- `node --check ui/answer-client.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - `23 passed`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` - `31 passed`
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` - `21 passed`
- `.venv/bin/python -m pytest -q` - `801 passed`
- `git diff --check`
- Protected-preview restart and local route checks
- Authenticated in-app browser smoke against the exact protected URL

## Integration Notes

Lane 15 should run full protected-preview smoke against:

`https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-expanded-keys-20260622`

The route is prepared for the expanded-key Explorer UI. This handoff does not certify full Explorer interaction coverage; it verifies the protected-preview route, cache-bust, expanded key selector presence, one non-G key switch, asset routing, and console cleanliness on the Explorer page.

## Risk Assessment

Risk: low.

The code change is limited to static script query strings and a matching frontend test assertion. Rollback is to restore the prior script query string `e9-explorer-expanded-key-ui-20260623` in `ui/e9-fretboard-explorer.html` and `tests/test_frontend_answer_ui.py`, then restart the protected-preview process.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-expanded-key-preview-refresh.md`

## Files That Must Not Be Staged

- Any unrelated dirty or untracked files shown by `git status --short`
- Corpus files
- Chroma/vector stores
- Embeddings
- Scraper output
- Private source data
- Auth, DNS, Cloudflare, or deployment configuration
- Brand/design assets

## Recommended Next Lane

Lane 15 QA / Answer Eval.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 15 should run full protected-preview browser smoke with:

```text
Lane: 15 QA / Answer Eval
Run full protected-preview smoke for the E9 Fretboard Explorer expanded-key UI at https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-expanded-keys-20260622. Verify all expanded keys, scale labels, row changes, advanced/core separation, warnings, per-string pedal/lever labels, and mobile usability.
```
