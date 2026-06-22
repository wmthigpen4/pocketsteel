# 2026-06-22 Lane 15 - E9 Fretboard Explorer User-Smoke Protected Preview

## Task Summary

Lane 15 ran protected-preview browser smoke for the E9 Fretboard Explorer user-smoke UI fixes from commit `7622a9b`.

Requested protected URL:

`https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-user-smoke-fixes-20260622`

This was a QA/browser-smoke task only. No app code, corpus data, embeddings, Chroma/vector data, scraper output, deployment/auth/DNS settings, assets, or private source data were changed.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-user-smoke-fixes-20260622`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-user-smoke-fixes-20260622`
- Exact URL the user should use: not recommended yet; protected preview appears stale for this slice
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded in the in-app browser
- Local backend URL: not used
- Expected backend port: not applicable
- Expected git HEAD: `7622a9b`
- Version endpoint: `https://app.steelguitarrag.com/api/version`
- Version endpoint result: not verified; browser navigation to `/api/version` was blocked by the browser client, and unauthenticated shell `curl` was redirected to Cloudflare Access
- If version endpoint missing, how version is inferred: DOM script URLs and smoke behavior were inspected; they indicate stale protected-preview assets
- Whether app root `/` works: not tested for this task
- Whether app root `/` is expected to work: not relevant to this Explorer smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested for this task
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not relevant to this Explorer smoke
- Who should test this URL: Codex after protected-preview refresh; user smoke should wait
- Do not test these URLs: do not use the root URL as proof of Explorer behavior
- Known caveats: the requested HTML URL loaded, but its internal Explorer scripts still used the older `e9-explorer-browser-surface-20260622` cache-bust

## Pass/Warn/Fail

Fail for protected-preview user-smoke readiness.

The page authenticated and loaded, and the local committed test baseline is green. However, the protected preview did not appear to serve the `7622a9b` user-smoke-fix assets. The same user-smoke issues remained visible in the protected page.

## Commit Under Test

- Current branch: `feature/answer-api`
- Current HEAD: `7622a9b`
- Protected-preview runtime version: not confirmed through `/api/version`
- Protected page asset evidence:
  - `pedal-steel-fretboard.js?v=e9-explorer-browser-surface-20260622`
  - `e9-fretboard-explorer-data.js?v=e9-explorer-browser-surface-20260622`
  - `e9-fretboard-explorer.js?v=e9-explorer-browser-surface-20260622`

The URL query string was the requested user-smoke-fix cache-bust, but the internal script cache-busts were still from the earlier browser-surface slice.

## Browser Smoke Results

| Check | Result |
| --- | --- |
| Protected URL loads after Cloudflare Access | Pass |
| Page is E9 Fretboard Explorer, not Access login | Pass |
| Controls render | Pass |
| G major rows render | Pass |
| 2-string mode uses only valid 2-string groups | Fail |
| 3-string mode shows core/advanced groups | Pass |
| Advanced groups include `5-6-7`, `6-7-10`, `5-7-8` | Pass |
| `5-7-8` appears as advanced / E-lower pocket | Pass |
| G natural minor display shows `G A Bb C D Eb F` | Pass |
| Bad minor display `G A A# C D D# F` absent | Pass |
| Natural minor avoids stale blank state | Fail |
| Dense SVG labels suppressed | Fail |
| Full row text remains in cards/details | Pass |
| Partial diminished / partial m7b5 warnings visible | Pass |
| Per-string pedal/lever changes visible | Pass |
| No `[object Object]` | Pass |
| Console errors | Pass, no errors observed |
| Fretboard background asset route observed | Pass, page assets included `/brand/pedal-steel-fretboard-background.svg` |
| Mobile/narrow viewport usable enough for MVP | Warn, usable controls and no document-level horizontal overflow, but stale label/filter failures remain |

## Mode-Aware Filter Results

Initial major / 3-string state:

- Row cards: `34`
- Groups shown in cards: `3-4-5`, `4-5-6`, `5-6-7`, `5-6-8`, `5-7-8`, `6-7-10`, `6-8-10`
- Group selector options: `All 3-string groups`, core groups, advanced groups
- SVG highlight labels observed: `34`

After selecting `2-string harmonized scale`:

- Row cards: `40`
- Card rows themselves used 2-string groups: `3-4`, `3-5`, `4-6`, `5-6`, `6-10`
- String-group selector still showed only stale 3-string choices:
  - `All 3-string groups`
  - `3-4-5`
  - `4-5-6`
  - `5-6-8`
  - `6-8-10`
  - `5-6-7`
  - `6-7-10`
  - `5-7-8`
- 2-string-specific options such as `3-5` were not selectable.
- SVG highlight labels observed: `40`

After selecting `3-string diatonic harmony`:

- Row cards: `34`
- Core and advanced groups were present.
- Advanced groups included `5-6-7`, `6-7-10`, and `5-7-8`.

After selecting `5-7-8`:

- Row cards: `2`
- Card kind: `Advanced swap - E-lower pocket`
- Per-string E-lower detail remained visible.
- SVG highlight labels observed: `2`

## Natural-Minor Behavior

From a stale 2-string / `5-7-8` selection, switching to `G natural minor` produced a blank row state:

- Scale display: `G A Bb C D Eb F`
- Bad display sequence absent: `G A A# C D D# F`
- Harmony mode remained `two_string_harmonized`
- String group remained stale `5-7-8`
- Row cards: `0`
- Highlight dots: `0`

This fails the requested behavior that G natural minor should disable or switch away from unavailable 2-string mode and avoid a blank stale state.

## Fretboard Label-Density Result

Fail.

Dense SVG text labels were still present on the Explorer surface:

- Initial 3-string view: `34` labels
- 2-string view: `40` labels
- `5-7-8` filtered view: `2` labels

The protected page did not appear to include the Lane 06 `showHighlightLabels: false` fix.

## Asset Routing Result

Pass for asset availability.

The browser page asset inventory observed:

- `https://app.steelguitarrag.com/brand/pedal-steel-fretboard-background.svg`

No console error was observed for the asset.

## Console Errors

No browser console errors or warnings were observed during the protected-preview smoke.

## Mobile / Narrow Viewport Result

Warn.

At `390x844`:

- Controls were visible.
- Document-level horizontal overflow was not present: `clientWidth=390`, `scrollWidth=390`.
- Fretboard SVG was present and horizontally scrollable inside its container.
- Stale failures remained:
  - internal scripts still used the old `e9-explorer-browser-surface-20260622` cache-bust
  - SVG highlight labels were still present
  - string-group selector still used stale 3-string options

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

Observed focused results:

- `tests/test_pedal_steel_fretboard_ui.py -q`: `31 passed`
- `tests/test_frontend_answer_ui.py -q`: `23 passed`
- `tests/test_fretboard_explorer.py -q`: `11 passed`
- full pytest: `791 passed`
- `git diff --check`: passed

## Files Changed

Created:

- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-user-smoke-protected-preview.md`

No implementation files were changed.

## Issues Found

1. Protected preview appears stale for the user-smoke UI fixes.
   - The exact protected URL loaded, but internal script URLs still used `e9-explorer-browser-surface-20260622`.
   - This likely explains why the user-smoke fixes were not visible.

2. 2-string mode selector did not rebuild to valid 2-string groups.
   - The rows changed to 2-string rows, but the selector still showed stale 3-string groups.

3. G natural minor could still land in a blank stale state.
   - Switching from stale 2-string / `5-7-8` to natural minor produced `0` cards and `0` dots.

4. Dense SVG text labels were still rendered on the Explorer surface.
   - This contradicts the reported Lane 06 label-density fix.

## Blockers

User smoke should remain blocked for this Explorer URL until protected preview serves the `7622a9b` Explorer HTML and script assets.

This is likely a protected-preview/static asset refresh or cache-bust issue, not evidence that the committed local code/test baseline is broken.

## Risks

Risk: medium.

The committed tests pass, but the protected preview currently does not reflect the expected user-smoke-fix behavior. Allowing user smoke on the tested URL would reproduce known stale UI failures.

## Human Decision Needed

No product decision needed.

Operational follow-up is needed from Lane 12 / Lane 06 to refresh or redeploy the protected-preview Explorer surface so the page HTML references the `7622a9b` user-smoke-fix assets.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-user-smoke-protected-preview.md`

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
- unrelated modified docs/scripts already present in the worktree

## Recommended Next Lane

Lane 12 Self-Hosted Deployment, with Lane 06 support if the static Explorer HTML cache-bust needs another UI patch.

## Commit Readiness

Safe to commit for this QA handoff only.

The product/user-smoke slice is not ready for user smoke on protected preview.

## Suggested Next Step

Prompt for Lane 12:

```text
Lane 12: Refresh the protected-preview E9 Fretboard Explorer surface for commit 7622a9b. The protected URL loads but still references e9-explorer-browser-surface-20260622 script assets instead of the user-smoke-fix assets. Verify /api/version if available, confirm the Explorer HTML references the current cache-busted scripts, and rerun Lane 15 protected-preview smoke for:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-user-smoke-fixes-20260622
Do not change DNS, corpus, Chroma, embeddings, auth policy, private data, or unrelated static assets.
```
