# E9 Fretboard Explorer Tooltip Detail Protected Preview Refresh

## Task Summary

Lane 12 was asked to refresh protected-preview static asset cache-busts for the E9 Fretboard Explorer tooltip/detail UX slice from `3aaae9a` or later, then verify the protected-preview route serves the new assets.

Completed:
- Updated only the Explorer HTML internal script query strings to `e9-explorer-tooltip-detail-ux-20260622`.
- Updated the narrow frontend test expectation that pins those script query strings.
- Verified local same-origin preview serves the refreshed script references.
- Ran the required JS, focused pytest, full pytest, and whitespace checks.
- Restarted the protected-preview process on `127.0.0.1:8770` after the scoped cache-bust commit.
- Verified the exact protected-preview Explorer URL loads with the refreshed assets after Cloudflare Access.
- Verified `/brand/pedal-steel-fretboard-background.svg` routing on protected preview.

Intentionally not changed:
- Product logic.
- Explorer filter/tooltip/detail behavior.
- Backend routing.
- Auth, DNS, Cloudflare Access, or deployment configuration.
- Corpus, embeddings, Chroma/vector stores, scraper output, private source data, raw assets, or unrelated dirty/untracked files.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-tooltip-detail-ux-20260622`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-tooltip-detail-ux-20260622`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-tooltip-detail-ux-20260622`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded in authenticated in-app browser context
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: scoped cache-bust commit created by this task, based on `3aaae9a`
- Version endpoint: `/api/version`
- Version endpoint result: local protected-preview endpoint reported the scoped cache-bust commit SHA on `feature/answer-api`
- If version endpoint missing, how version is inferred: not missing locally; protected page asset inventory also confirmed refreshed script URLs
- Whether app root `/` works: not tested for this Explorer-specific smoke
- Whether app root `/` is expected to work: not required for this task
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes, but out of scope
- Who should test this URL: Lane 15 and the user
- Do not test these URLs: stale Explorer URLs using `e9-explorer-user-smoke-fixes-20260622b` or older cache-busts
- Known caveats: direct protected browser navigation to `/api/version` can be blocked by the browser client; local protected-preview `/api/version` was used for runtime identity.

## Root Cause

`ui/e9-fretboard-explorer.html` still referenced the prior internal script cache-bust:

- `pedal-steel-fretboard.js?v=e9-explorer-user-smoke-fixes-20260622b`
- `e9-fretboard-explorer-data.js?v=e9-explorer-user-smoke-fixes-20260622b`
- `e9-fretboard-explorer.js?v=e9-explorer-user-smoke-fixes-20260622b`

The outer URL cache-bust alone would not force browsers to reload those internally referenced scripts.

## Files Changed

- Modified: `ui/e9-fretboard-explorer.html`
- Modified: `tests/test_frontend_answer_ui.py`
- Created: `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-tooltip-detail-preview-refresh.md`
- Deleted files: none
- Generated artifacts: none

## Cache-Bust Result

Pass.

Local and protected-preview HTML now reference:

- `pedal-steel-fretboard.js?v=e9-explorer-tooltip-detail-ux-20260622`
- `e9-fretboard-explorer-data.js?v=e9-explorer-tooltip-detail-ux-20260622`
- `e9-fretboard-explorer.js?v=e9-explorer-tooltip-detail-ux-20260622`

## Protected Preview Refresh Result

Pass.

The protected-preview process was restarted using the existing detached `screen` workflow for the Mac-hosted preview. The process listened on `127.0.0.1:8770`, and local `/api/version` reported the scoped cache-bust commit SHA on `feature/answer-api`.

## Asset Routing Result

Pass.

Protected-preview page asset inventory included:

- `https://app.steelguitarrag.com/brand/pedal-steel-fretboard-background.svg`

This verifies the `/brand/` route that the temporary local static server did not mount.

## Quick Browser Checks

Pass.

Verified in the authenticated protected-preview browser:

- Page is `E9 Fretboard Explorer`.
- `Showing validated positions` appears.
- `validated rows` no longer appears in primary body copy.
- `E-lower+E-lower` does not appear.
- Marker/detail tooltip UX is present enough for Lane 15 full smoke:
  - selectable row buttons present;
  - selected detail panel present;
  - marker nodes expose `role="button"`, `tabindex="0"`, accessible labels, and titles.
- G natural minor spelling remains `G A Bb C D Eb F`.
- `[object Object]` absent.
- Console errors absent.

## Tests and Checks

Commands run:

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
rg "e9-explorer-" ui/e9-fretboard-explorer.html
node --check ui/e9-fretboard-explorer.js
node --check ui/e9-fretboard-explorer-data.js
node --check ui/pedal-steel-fretboard.js
node --check ui/answer-client.js
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
.venv/bin/python -m pytest -q
git diff --check
curl -sS "http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=e9-explorer-tooltip-detail-ux-20260622" | grep -nE "pedal-steel-fretboard|e9-fretboard-explorer"
curl -sS http://127.0.0.1:8770/api/version
```

Results:

- JS syntax checks: passed.
- `tests/test_frontend_answer_ui.py -q`: 23 passed.
- `tests/test_pedal_steel_fretboard_ui.py -q`: 31 passed.
- `tests/test_fretboard_explorer.py -q`: 11 passed.
- Full pytest: 791 passed.
- `git diff --check`: passed.
- Local served HTML showed the refreshed tooltip/detail UX cache-busts.
- Protected browser smoke passed at the exact target URL.

## Integration Notes

This is a cache-bust/protected-preview refresh only. The actual tooltip/detail UX behavior was implemented by Lane 06 in `3aaae9a`; this Lane 12 task only made protected preview load that slice reliably.

Lane 15 can now run full protected-preview smoke at:

`https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-tooltip-detail-ux-20260622`

## Risk Assessment

Risk: low.

Reason:
- Static query-string refresh only, plus a matching test expectation and handoff.
- Full test suite passed.
- Protected-preview browser smoke verified the refreshed asset routing.

Rollback:
- Revert this scoped cache-bust commit or update the Explorer HTML to a newer cache-bust if another UI slice lands.

## Human Decision Needed

No.

## Safe-to-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-tooltip-detail-preview-refresh.md`

## Files That Must Not Be Staged

- Unrelated dirty work shown by `git status --short`.
- `README.md`
- `corpus_metadata/`
- `source-inbox/`
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores
- embeddings
- scraper output
- `.wrangler/`
- DNS/auth/secrets files
- `public/`
- `ui/brand/`
- `Neon Sign/`
- raw visual/design assets

## Recommended Next Lane

Lane 15 QA / Answer Eval.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 15: run full protected-preview E9 Fretboard Explorer smoke at `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-tooltip-detail-ux-20260622`, focusing on marker tooltip/detail behavior, row buttons, selected detail panel, natural minor spelling, deduped pedal/lever labels, `/brand/` asset routing, and mobile/narrow usability.
