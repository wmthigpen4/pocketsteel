# 2026-06-22 Lane 15 - E9 Fretboard Explorer Final Protected Smoke

## Task Summary

Lane 15 reran the full protected-preview E9 Fretboard Explorer smoke after Lane 12 refreshed the Explorer asset cache-busts.

Tested protected URL:

`https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-user-smoke-fixes-20260622b`

This was QA/browser smoke only. No app code, corpus data, embeddings, Chroma/vector data, scraper output, deployment/auth/DNS settings, assets, or private source data were changed.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-user-smoke-fixes-20260622b`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-user-smoke-fixes-20260622b`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-user-smoke-fixes-20260622b`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded in the in-app browser
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `c1bea83`
- Version endpoint: `/api/version`
- Version endpoint result: local protected-preview endpoint returned `c1bea83` on `feature/answer-api`; direct protected browser navigation to `/api/version` returned `net::ERR_BLOCKED_BY_CLIENT`
- If version endpoint missing, how version is inferred: not missing locally; protected page script asset URLs also confirm the refreshed `e9-explorer-user-smoke-fixes-20260622b` cache-bust
- Whether app root `/` works: not tested for this Explorer-specific smoke
- Whether app root `/` is expected to work: not required for this task
- Whether `/ui/steel-guitar-rag-mock.html` works: yes, checked for the Explorer entry link
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: the user and Lane 15
- Do not test these URLs: stale Explorer URLs with `?v=e9-explorer-browser-surface-20260622` or `?v=e9-explorer-user-smoke-fixes-20260622`
- Known caveats: browser-client direct navigation to protected `/api/version` is blocked; local protected-preview `/api/version` was used for commit identity

## Pass / Warn / Fail

Pass.

The refreshed protected-preview Explorer surface now serves the `e9-explorer-user-smoke-fixes-20260622b` script assets and passes the full requested Lane 15 user-smoke checklist, including mobile/narrow viewport.

## Commit / Version Result

- Current branch: `feature/answer-api`
- Current HEAD at task start: `c1bea83`
- Local protected-preview `/api/version`:

```json
{"git_sha":"c1bea83","git_branch":"feature/answer-api","python_module":"steel_guitar_rag.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}
```

- Direct browser navigation to `https://app.steelguitarrag.com/api/version` was blocked by the browser client with `net::ERR_BLOCKED_BY_CLIENT`.

## Refreshed Asset / Cache-Bust Result

Pass.

The protected Explorer page loaded these refreshed script URLs:

- `https://app.steelguitarrag.com/ui/pedal-steel-fretboard.js?v=e9-explorer-user-smoke-fixes-20260622b`
- `https://app.steelguitarrag.com/ui/e9-fretboard-explorer-data.js?v=e9-explorer-user-smoke-fixes-20260622b`
- `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.js?v=e9-explorer-user-smoke-fixes-20260622b`

No protected-page script URL used the stale `e9-explorer-browser-surface-20260622` cache-bust.

## Browser Smoke Results

| Check | Result |
| --- | --- |
| Exact protected URL loads after Cloudflare Access | Pass |
| Page is E9 Fretboard Explorer, not Access login | Pass |
| Key selector renders | Pass |
| Scale selector renders | Pass |
| Harmony/view selector renders | Pass |
| String-group selector renders | Pass |
| G major rows render | Pass |
| 2-string harmonized scale shows only valid 2-string groups | Pass |
| 2-string mode excludes 3-string groups | Pass |
| 2-string mode does not blank the fretboard | Pass |
| 3-string diatonic harmony shows valid 3-string groups | Pass |
| Core and advanced groups are separated | Pass |
| Advanced groups include `5-6-7`, `6-7-10`, `5-7-8` | Pass |
| `5-7-8` appears as advanced / E-lower pocket | Pass |
| G natural minor switches/disables unavailable 2-string state | Pass |
| G natural minor avoids blank stale state | Pass |
| Scale display shows `G A Bb C D Eb F` | Pass |
| Bad display `G A A# C D D# F` absent | Pass |
| All string groups show marker/dot output without dense text labels | Pass |
| Full row text remains in cards/details | Pass |
| Partial diminished / partial m7b5 warnings visible | Pass |
| Per-string pedal/lever changes visible | Pass |
| `Eb/D#` visible where mechanically appropriate | Pass |
| No `[object Object]` | Pass |
| No console errors or warnings | Pass |
| `/brand/pedal-steel-fretboard-background.svg` loads | Pass |
| Mock/landing surface includes `Explore the E9 Fretboard` | Pass |
| Mobile/narrow viewport around 390x844 usable | Pass |

## Mode-Aware Filter Results

Initial G major / 3-string state:

- Row cards: `34`
- Groups in cards: `3-4-5`, `4-5-6`, `5-6-7`, `5-6-8`, `5-7-8`, `6-7-10`, `6-8-10`
- Card kinds: `Core grip`, `Advanced swap`, `Advanced swap - E-lower pocket`
- Highlight dots: `102`
- Highlight labels: `0`

After selecting `2-string harmonized scale`:

- Row cards: `40`
- String-group selector options:
  - `All 2-string groups`
  - `3-5`
  - `5-6`
  - `6-10`
  - `4-6`
  - `3-4`
- 3-string groups were absent from the selector.
- Card groups: `3-4`, `3-5`, `4-6`, `5-6`, `6-10`
- Highlight dots: `80`
- Highlight labels: `0`

Specific 2-string group `3-5`:

- Selectable.
- Row cards: `8`
- Card groups: `3-5`
- Highlight labels: `0`

After selecting `3-string diatonic harmony`:

- Row cards: `34`
- String-group selector returned to valid 3-string groups.
- Advanced groups included `5-6-7`, `6-7-10`, and `5-7-8`.

Specific advanced group `5-7-8`:

- Row cards: `2`
- Card kind: `Advanced swap - E-lower pocket`
- Per-string changes visible.
- `Eb/D#` visible in the E-lower mechanical detail.
- Highlight labels: `0`

## Natural-Minor Behavior

Pass.

Switching to `G natural minor` from 2-string mode:

- Disabled `2-string harmonized scale`.
- Switched harmony value to `three_string_diatonic`.
- Reset string group to `all`.
- Displayed `32` row cards.
- Displayed `G A Bb C D Eb F`.
- Did not display `G A A# C D D# F`.
- Excluded unavailable `5-7-8` from natural-minor group options.
- Did not produce a blank stale state.
- Highlight labels remained `0`.

## Fretboard Label-Density Result

Pass.

Observed SVG/fretboard highlight label count:

- Initial 3-string view: `0`
- 2-string view: `0`
- `3-5` 2-string filtered view: `0`
- `5-7-8` advanced filtered view: `0`
- Natural minor all-groups view: `0`
- Mobile/narrow viewport: `0`

Marker/dot counts remained nonzero where rows were visible.

## Asset Routing Result

Pass.

Protected page asset inventory included:

- `https://app.steelguitarrag.com/brand/pedal-steel-fretboard-background.svg`

The page asset inventory reported the asset as an image resource, and no asset-related console errors were observed.

## Console Errors

Pass.

No console errors or warnings were observed during:

- desktop protected Explorer smoke
- interaction smoke
- mock entry check
- mobile/narrow viewport smoke

## Landing Entry Result

Pass.

Checked:

`https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=e9-explorer-user-smoke-fixes-20260622b`

Observed:

- Page loaded after Cloudflare Access.
- `Explore the E9 Fretboard` was present.
- Link target: `e9-fretboard-explorer.html`
- No `[object Object]`.

## Mobile / Narrow Viewport Result

Pass.

At `390x844`:

- Four selector controls were visible.
- Selectors were `336px` wide and fit the viewport.
- No document-level horizontal overflow:
  - `clientWidth=390`
  - `scrollWidth=390`
  - `bodyScrollWidth=390`
- Fretboard SVG was present.
- Fretboard SVG measured `700px` wide inside its scrollable/contained region.
- Row cards: `34`
- Highlight dots: `102`
- Highlight labels: `0`
- No `[object Object]`.
- No console errors or warnings.

## Automated Tests Run

Passed:

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
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

Observed results:

- `node --check ...`: passed.
- `tests/test_pedal_steel_fretboard_ui.py -q`: `31 passed`
- `tests/test_frontend_answer_ui.py -q`: `23 passed`
- `tests/test_fretboard_explorer.py -q`: `11 passed`
- full pytest: `791 passed`
- `git diff --check`: passed

## Files Changed

Created:

- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-final-protected-smoke.md`

No implementation files were changed.

## Issues Found

None.

The previous protected-preview stale-asset failures were cleared by the Lane 12 refresh.

## Blockers

None for the E9 Fretboard Explorer protected-preview smoke.

## Risks

Risk: low.

The protected-preview smoke now matches the requested behavior, and the local automated test suite is green. Remaining risk is ordinary user-smoke coverage beyond the checked Explorer flows.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-final-protected-smoke.md`

## Files That Must Not Be Staged

Do not stage unrelated dirty/untracked files, especially:

- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores
- embeddings
- scraper/corpus output
- `source-inbox/`
- `.wrangler/`
- deployment/auth/DNS config
- `public/`
- `ui/brand/`
- `Neon Sign/`
- raw design assets
- unrelated modified docs/scripts/reports already present in the worktree

## Recommended Next Lane

Lane 01 Repo Steward or user smoke continuation.

## Commit Readiness

Safe to commit for this QA handoff only.

The E9 Fretboard Explorer protected-preview surface is ready for user smoke at:

`https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-user-smoke-fixes-20260622b`

## Suggested Next Step

Prompt for Lane 01:

```text
Lane 01: Record the E9 Fretboard Explorer final protected-preview smoke result from docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-final-protected-smoke.md in integration-status.md if the current coordination snapshot needs a refresh. Do not stage unrelated dirty files.
```
