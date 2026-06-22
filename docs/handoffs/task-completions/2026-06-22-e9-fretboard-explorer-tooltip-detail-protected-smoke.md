# E9 Fretboard Explorer Tooltip Detail Protected Smoke

## Task Summary

Lane 15 ran protected-preview browser smoke for the E9 Fretboard Explorer tooltip/detail UX slice after the protected-preview cache-bust refresh containing `3aaae9a fix: improve e9 explorer marker details`.

Completed:
- Verified the protected Explorer URL loads after existing Cloudflare Access authentication.
- Verified cache-busted Explorer scripts use `e9-explorer-tooltip-detail-ux-20260622`.
- Verified tooltip/detail behavior, marker accessibility metadata, mode-aware filters, natural-minor spelling, label-density cleanup, `5-7-8` E-lower detail behavior, and mobile/narrow viewport behavior.
- Ran requested automated checks, including full pytest.

Intentionally not changed:
- No app code, UI implementation, corpus, Chroma, embeddings, scraper output, deployment, auth, DNS, assets, private source data, or unrelated dirty files were modified.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-tooltip-detail-ux-20260622`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-tooltip-detail-ux-20260622`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-tooltip-detail-ux-20260622`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded via existing authenticated browser session
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `d9afa2b` or later containing `3aaae9a`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `{"git_sha":"d9afa2b","git_branch":"feature/answer-api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}`
- If version endpoint missing, how version is inferred: not needed; endpoint responded
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not required for this Explorer smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested in this task
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not required for this Explorer smoke
- Who should test this URL: both Codex and the user
- Do not test these URLs: uncached Explorer URLs or app root as a substitute for this smoke target
- Known caveats: direct protected-preview browser smoke was used for the Explorer page; no API fallback was used for UI behavior

## Pass/Warn/Fail

Pass.

No product blockers were found in the protected-preview Explorer tooltip/detail smoke.

Warn:
- The browser dev-log API retained one old console error after a standalone SVG asset probe: `TypeError: Cannot use 'in' operator to search for 'animation' in undefined`. The timestamp matched the separate asset-tab check. The Explorer page itself loaded and interacted correctly, with no observed new Explorer-specific console errors during the UI smoke.

## Commit Under Test

- Current branch: `feature/answer-api`
- Current HEAD: `d9afa2b fix: refresh e9 explorer tooltip asset cache-bust`
- Relevant implementation commit included: `3aaae9a fix: improve e9 explorer marker details`

Recent log context:
- `d9afa2b fix: refresh e9 explorer tooltip asset cache-bust`
- `3aaae9a fix: improve e9 explorer marker details`
- `7c56156 docs: record E9 explorer final protected smoke`
- `c1bea83 fix: refresh e9 explorer preview asset cache-bust`

## Browser Smoke Results

### Access, Version, And Assets

Pass.

- Exact protected URL loaded.
- Page title was `E9 Fretboard Explorer - Steel Guitar RAG`.
- Page showed `E9 Fretboard Explorer`, not a Cloudflare Access login page.
- Version endpoint reported `d9afa2b`.
- Script cache-busts observed:
  - `pedal-steel-fretboard.js?v=e9-explorer-tooltip-detail-ux-20260622`
  - `e9-fretboard-explorer-data.js?v=e9-explorer-tooltip-detail-ux-20260622`
  - `e9-fretboard-explorer.js?v=e9-explorer-tooltip-detail-ux-20260622`
- Protected asset route `/brand/pedal-steel-fretboard-background.svg` loaded as an SVG document.

### Header And Summary

Pass.

- `Showing validated positions` appeared.
- The primary copy did not show `N validated rows`.
- `[object Object]` was absent.
- The page copy still explicitly says the Explorer uses validated rows, not corpus retrieval or RAG-generated fretboard positions. That is correct and prevents implying RAG generated the deterministic Explorer positions.

### Mode-Aware Filters

Pass.

- In `2-string harmonized scale`, the string-group selector rebuilt to valid 2-string groups only:
  - `All 2-string groups`
  - `3-5`
  - `5-6`
  - `6-10`
  - `4-6`
  - `3-4`
- No 3-string core groups appeared in 2-string mode.
- The fretboard did not go blank after switching modes.
- In `3-string diatonic harmony`, the selector rebuilt to valid 3-string groups:
  - Core: `3-4-5`, `4-5-6`, `5-6-8`, `6-8-10`
  - Advanced: `5-6-7`, `6-7-10`, `5-7-8`

### Natural Minor Behavior

Pass.

- Switching to `G natural minor` from 2-string mode automatically moved to valid 3-string rows.
- The unavailable 2-string mode was disabled.
- No blank stale state appeared.
- Scale display showed `G A Bb C D Eb F`.
- Bad spelling sequence `G A A# C D D# F` was absent.

### Label Density

Pass.

- SVG markers rendered as compact dots/buttons.
- Dense permanent row text was not stacked on the fretboard.
- Marker nodes had empty text content while detail text remained available through row buttons and the detail panel.
- All-groups views remained readable enough for this protected-preview smoke.

### Tooltip And Detail UX

Pass.

- Marker nodes expose `role="button"` and `tabindex="0"`.
- Marker title and ARIA text include compact teaching details such as chord/function, fret, string group, display notes, pedals/levers, and warnings where applicable.
- Click/focus/keyboard interaction exposed a tooltip/detail state.
- Tooltip/detail examples included:
  - `Fret 1 · strings 3-4-5`
  - `Notes: 3: Bb; 4: G; 5: D`
  - `Pedals/levers: B, C`
  - Warning text for partial diminished rows: `This grip contains 1-b3-b5 only... does not include the b7.`
- Keyboard `Enter` on a focused marker preserved detail behavior.
- Tooltip/detail content was compact and did not obscure the whole board in the tested desktop viewport.

### 5-7-8 E-Lower Details

Pass.

- `5-7-8` appeared as an advanced E-lower pocket.
- `E-lower+E-lower` was absent.
- `E-lower` label appeared once.
- `Eb/D#` appeared in the `5-7-8` detail path.
- Per-string change detail remained visible, for example string 8 controls `E-lower` from `E` to `Eb/D#`.

### Partial Diminished / m7b5 Warnings

Pass.

- Partial diminished / partial m7b5 warning text remained visible in tooltip/detail state.
- Three-note 1-b3-b5 grips were not presented as full m7b5 without the missing b7 warning.

### Mobile / Narrow Viewport

Pass.

Tested around `390x844`.

- Controls were visible and fit within the viewport.
- No document-level horizontal overflow was detected (`documentElement.scrollWidth` matched viewport width).
- Fretboard was present and horizontally scrollable inside its own area.
- Marker labels stayed suppressed; no dense label pile-up appeared.
- Detail buttons/panel remained usable enough for MVP.

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
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
.venv/bin/python -m pytest -q
git diff --check
```

Results:
- `tests/test_frontend_answer_ui.py -q`: 23 passed
- `tests/test_pedal_steel_fretboard_ui.py -q`: 31 passed
- `tests/test_fretboard_explorer.py -q`: 11 passed
- Full pytest: 791 passed
- `git diff --check`: passed

## Files Changed

Created:
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-tooltip-detail-protected-smoke.md`

No implementation files were modified.

## Issues Found

None blocking.

Non-blocking caveat:
- A retained browser dev-log entry appeared after loading the standalone SVG asset route. It did not correlate with Explorer interaction and did not block the Explorer UI smoke.

## Blockers

None.

## Risks

Low.

The smoke covered the protected-preview Explorer surface, cache-busted assets, desktop and mobile states, mode-aware filters, natural-minor spelling, marker detail behavior, and focused/full automated checks. Risk remains that a separate browser/device may surface visual polish differences, but no release-blocking functional issue was found.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-tooltip-detail-protected-smoke.md`

## Files That Must Not Be Staged

All unrelated dirty or untracked files, including but not limited to:
- corpus/private/vector/embedding outputs
- scraper output
- deployment/auth/DNS files
- UI implementation files
- design/raw asset files
- unrelated docs and handoffs already present in the worktree

## Recommended Next Lane

Lane 01 Repo Steward.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 01 should record or verify the scoped QA handoff commit if needed, then allow user smoke to continue on:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-tooltip-detail-ux-20260622
```
