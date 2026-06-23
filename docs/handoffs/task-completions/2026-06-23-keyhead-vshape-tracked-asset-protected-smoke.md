# 2026-06-23 Keyhead V-Shape Tracked Asset Protected Smoke

## Task Summary

Lane 12 verified that protected preview serves the now-tracked V-shaped pedal-steel fretboard background SVG asset after Lane 01 committed `bce771f fix: track fretboard keyhead asset`.

Completed:
- Confirmed `public/brand/pedal-steel-fretboard-background.svg` is tracked.
- Confirmed `/api/version` reports `bce771f` on `feature/answer-api`.
- Verified the protected SVG URL loads through Cloudflare Access.
- Verified SVG structure: `viewBox`, no root `width` / `height`, V-shaped keyhead shell, 10 tuners, 5 top / 5 bottom.
- Verified the protected E9 Fretboard Explorer route loads and references `/brand/pedal-steel-fretboard-background.svg`.
- Verified explanation UI and expanded keys remain available.
- Ran requested syntax and focused frontend tests.

Intentionally not changed:
- No product logic, UI behavior, corpus, Chroma/vector stores, embeddings, scraper output, auth, DNS, deployment config, private source data, or assets were modified.
- The parked Lane 01 closeout handoff `docs/handoffs/task-completions/2026-06-23-01-keyhead-vshape-asset-commit.md` was left unstaged.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f`
- Cache-busted URL tested: `https://app.steelguitarrag.com/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f`
- Explorer URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-explanation-ui-20260623`
- Exact URL the user should use for asset smoke: `https://app.steelguitarrag.com/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f`
- Exact URL the user should use for Explorer smoke: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-explanation-ui-20260623`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; protected URLs loaded as product/static routes, not Access login pages
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `bce771f` or later containing tracked keyhead asset
- Version endpoint: `/api/version`
- Version endpoint result: `{"git_sha":"bce771f","git_branch":"feature/answer-api","python_module":"pocketsteel.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}`
- If version endpoint missing, how version is inferred: not missing
- Whether app root `/` works: not tested for this task
- Whether app root `/` is expected to work: not required for this task
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested for this task
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes, but outside this task's scope
- Who should test this URL: Lane 15 / the user if visual confirmation is desired
- Do not test these URLs: uncached SVG or Explorer URLs for this slice
- Known caveats: raw SVG browser tab logs a browser-runtime promise warning; this is recorded separately from Explorer app-page rendering.

## Pass / Warn / Fail

PASS with raw-SVG-tab caveat.

The tracked asset is committed, served by protected preview, and referenced by the Explorer route. The Explorer route rendered normally. The raw SVG tab emitted the known browser-runtime promise warning after loading the standalone SVG, but the SVG loaded and Explorer rendering was not blocked.

## Exact URLs Tested

- `https://app.steelguitarrag.com/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f`
- `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-explanation-ui-20260623`

## Auth Result

PASS. Cloudflare Access session succeeded. Neither protected URL landed on an Access login page.

## Version / Commit Result

PASS.

- Current branch: `feature/answer-api`
- Current HEAD: `bce771f fix: track fretboard keyhead asset`
- Local `/api/version`: `bce771f`
- Tracked asset check: `git ls-files -- public/brand/pedal-steel-fretboard-background.svg` returned `public/brand/pedal-steel-fretboard-background.svg`
- Asset history check: `git log --oneline -- public/brand/pedal-steel-fretboard-background.svg` includes `bce771f fix: track fretboard keyhead asset`

## Tracked Asset Result

PASS.

`public/brand/pedal-steel-fretboard-background.svg` is tracked in git and included in commit `bce771f`.

## Asset Routing Result

PASS.

The exact protected SVG URL loaded an SVG document:

- `svg` element present
- `viewBox`: `0 0 1600 420`
- root `width`: absent
- root `height`: absent
- Cloudflare Access login page: not present
- `data-layer="headstock-keyhead-shell"` present
- `data-layer="10-tuning-keys"` present

## Visual Result

PASS.

Observed protected SVG structure:

- V-shaped keyhead shell present.
- Tuner count: 10.
- Top tuner groups: 5.
- Bottom tuner groups: 5.
- Top tuner y-values by increasing x: `[135, 125, 115, 105, 95]`.
- Bottom tuner y-values by increasing x: `[271, 281, 291, 301, 311]`.
- Top and bottom rows taper in opposite directions, consistent with the V-shaped keyhead widening toward the roller-nut side.

## Explorer Result

PASS.

The protected Explorer route loaded and showed:

- `E9 Fretboard Explorer`
- `Showing validated positions`
- explanation UI present
- expanded keys available: `G`, `C`, `D`, `F`, `Bb`, `Eb`
- one embedded fretboard SVG
- in-page SVG image reference: `/brand/pedal-steel-fretboard-background.svg`
- no `[object Object]`

Loaded scripts used the expected explanation UI cache-bust:

- `pedal-steel-fretboard.js?v=e9-explorer-explanation-ui-20260623`
- `e9-fretboard-explorer-data.js?v=e9-explorer-explanation-ui-20260623`
- `e9-fretboard-explorer.js?v=e9-explorer-explanation-ui-20260623`

## Console Errors

PASS for Explorer rendering with caveat.

The raw SVG asset tab logged:

```text
Uncaught (in promise) TypeError: Cannot use 'in' operator to search for 'animation' in undefined
```

This occurred while viewing the standalone SVG asset. The SVG still loaded, and the Explorer app page rendered normally with the background reference, explanation UI, expanded keys, and no visible object-string/rendering failure.

## Tests Run

- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git ls-files -- public/brand/pedal-steel-fretboard-background.svg`
- `git log --oneline -- public/brand/pedal-steel-fretboard-background.svg`
- `node --check ui/pedal-steel-fretboard.js`
- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/e9-fretboard-explorer-data.js`
- `node --check ui/answer-client.js`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` - `31 passed`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - `23 passed`
- `curl -sS http://127.0.0.1:8770/api/version`
- Authenticated in-app browser smoke for the exact protected SVG URL
- Authenticated in-app browser smoke for the exact protected Explorer URL
- `git diff --check`

## Files Changed

Created:
- `docs/handoffs/task-completions/2026-06-23-keyhead-vshape-tracked-asset-protected-smoke.md`

No implementation, asset, corpus, Chroma, embedding, scraper, auth, DNS, deployment, or private-source files were changed.

## Risks

Low.

The asset is now tracked and protected preview reports runtime commit `bce771f`. The only caveat is the raw-SVG-tab browser-runtime warning, which does not currently block the Explorer route.

Rollback note: revert `bce771f` or restore the prior approved `public/brand/pedal-steel-fretboard-background.svg` geometry, then restart protected preview if the runtime needs to serve the rollback.

## Human Decision Needed

No for this Lane 12 verification.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-23-keyhead-vshape-tracked-asset-protected-smoke.md`

## Files That Must Not Be Staged

- `docs/handoffs/task-completions/2026-06-23-01-keyhead-vshape-asset-commit.md` unless Lane 01 explicitly includes it
- Any unrelated dirty or untracked files shown by `git status --short`
- Corpus files
- Chroma/vector stores
- Embeddings
- Scraper output
- Private source data
- Auth, DNS, Cloudflare, or deployment configuration
- Unapproved brand/design assets

## Recommended Next Lane

Lane 15 QA / Answer Eval or user visual smoke.

## Commit Readiness

Safe to commit.

## Recommended Next Prompt

```text
Lane 15 QA: Run a final browser visual smoke for the tracked V-shaped keyhead SVG in the E9 Fretboard Explorer at https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-explanation-ui-20260623. Confirm the keyhead/tuners remain visually acceptable in context and no Explorer UI regressions appear.
```
