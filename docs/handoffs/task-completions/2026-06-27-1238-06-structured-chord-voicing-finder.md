# 2026-06-27 12:38 - Lane 06 - Structured Chord / Voicing Finder

## Task Summary

Redesigned the E9 Fretboard Explorer Chord / Voicing Finder input so the main learner workflow no longer relies on a free-text chord parser. The finder now uses structured Root, Quality, and Pedals / levers scope controls. Parser utilities remain available internally for compatibility and rule tests, but the visible workflow no longer shows the `Target chord or function` input or normal-use parser errors.

Intentionally not changed:
- Backend chord, voicing, fretboard, or parser rules.
- Fretboard geometry, notation logic, harmonized-scale data, copedent data, corpus, Chroma, embeddings, auth, DNS, deployment config, or source/private data.
- Protected-preview runtime restart.

## Files Changed

- `ui/e9-fretboard-explorer.js`
  - Added structured chord-finder root options including sharp/flat spellings.
  - Added learner-facing quality labels: Major, Minor, Diminished, Half-diminished, Sus2, Sus4, Dominant 7, Major 7, Minor 7, Dominant 9, Minor 9, Major 9.
  - Changed default target from a free-text `Fmaj7` parser string to structured `F` + `Major 7`.
  - Removed the visible text-input event path from the Chord / Voicing Finder panel.
  - Kept explicit `parseChordFinderQuery("...")` compatibility for internal/shared-rule tests.
- `ui/e9-fretboard-explorer.html`
  - Reduced the Chord / Voicing Finder controls grid from a text-input-plus-three-controls layout to three structured controls.
  - Refreshed the Explorer script query string to `structured-chord-picker-20260627` so protected preview requests the updated renderer.
- `tests/test_frontend_answer_ui.py`
  - Updated focused tests to assert the free-text target field is absent.
  - Added structured Root/Quality control assertions and dropdown-driven Fmaj7, Cm9, and D7 behavior checks.

## Tests And Checks

Passed:

- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/e9-music-rules.js`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `node --check ui/e9-fretboard-explorer-data.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - 24 passed
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` - 34 passed
- `.venv/bin/python -m pytest tests/test_explorer_musical_red_team.py -q` - 4 passed
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` - 38 passed
- `.venv/bin/python -m pytest -q` - 861 passed
- `git diff --check`

## Local Browser Smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=structured-chord-picker-local`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=structured-chord-picker-local`
- Exact URL the user should use: protected-preview URL after Lane 12 refresh
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `a6abc61` before commit
- Version endpoint: not checked for local smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local worktree/browser file state
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not required for this Explorer-specific smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not required for this Explorer-specific smoke
- Who should test this URL: Codex locally, then the user after protected-preview smoke
- Do not test these URLs: uncache-busted Explorer URL for this change
- Known caveats: local browser smoke does not prove protected-preview cache freshness

Local browser result:
- Chord / Voicing Finder mode loads.
- No `explorer-chord-query` text input is present.
- Root options include sharp and flat spellings.
- Quality options show learner-facing labels.
- Default target is `Fmaj7`.
- `D` + `Dominant 7` shows `Target: D7`.
- `C` + `Minor 9` shows `Target: Cm9`; with expanded grip/scope filters it returns candidates.
- Candidate selection updates the selected detail and fretboard highlight state.
- No parser errors (`I could not read`, `Enter a chord`, `Try a chord symbol`) appear during normal picker use.
- No `[object Object]`.
- Console warnings/errors: none.

## Protected Preview Freshness Check

Initial protected-preview smoke target:

`https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=structured-chord-finder-452600e`

Result:
- Cloudflare Access session was already authenticated in the in-app browser.
- Explorer page loaded.
- The page still showed the old free-text `explorer-chord-query` because `ui/e9-fretboard-explorer.html` was still requesting `e9-fretboard-explorer.js?v=shared-music-rules-20260627`.
- Fixed within this slice by refreshing the Explorer script query string to `e9-fretboard-explorer.js?v=structured-chord-picker-20260627` and adding a focused test assertion.

Protected-preview browser smoke needs to be rerun after the amended commit with a new cache-busted URL.

## Integration Notes

- The main UI path is now structured-control-first.
- Existing explicit parser compatibility remains intact for tests and shared-rule utilities. This was necessary because existing tests still validate `parseChordFinderQuery("V7 in G")`, `parseChordFinderQuery("Imaj7 in F")`, and direct chord aliases.
- Function-in-key mode was not added as a visible UI mode in this slice. The existing parser still supports function strings internally, but the visible Chord / Voicing Finder now uses chord root/quality only. A future UI slice can add a separate `Chord` vs `Function in key` selector if product wants it.
- Protected-preview smoke showed why the script cache-bust matters for this page; the HTML now requests the refreshed Explorer JS.

## Risk Assessment

Risk: low to medium.

Why:
- The change is limited to frontend control rendering and tests.
- Backend/music-rule logic was not changed.
- Full pytest passed.
- Browser smoke verified the main structured-control workflow and candidate/fretboard selection.

Rollback:
- Revert the scoped commit touching `ui/e9-fretboard-explorer.js`, `ui/e9-fretboard-explorer.html`, `tests/test_frontend_answer_ui.py`, and this handoff.

## Human Decision Needed

No immediate decision needed.

Potential product follow-up:
- Decide whether to add a visible Function-in-key mode (`Key` + `Function` + `Quality`) as a separate structured workflow. This was not included to avoid widening the current slice.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-1238-06-structured-chord-voicing-finder.md`

## Files That Must Not Be Staged

- Existing unrelated dirty files shown by `git status --short`, including README/docs drift, corpus metadata, source-inbox files, RAG scripts, brand assets, `public/`, `ui/brand/`, `Neon Sign/`, private/source/generated paths, and unrelated untracked handoffs/assets.

## Recommended Next Lane

Lane 12 protected-preview smoke after commit, then user smoke.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 12:

Run protected-preview smoke against:

`https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=<commit-or-slice-cachebuster>`

Verify Chord / Voicing Finder has no free-text target field, Root/Quality controls work for F Major 7, C Minor 9, and D Dominant 7, candidate selection updates the fretboard, and no parser error or `[object Object]` appears.
