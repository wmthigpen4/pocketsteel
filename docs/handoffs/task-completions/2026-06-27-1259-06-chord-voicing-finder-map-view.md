# 2026-06-27 12:59 - Lane 06 - Chord / Voicing Finder Map View

## Task Summary

Requested: make the E9 Fretboard Explorer Chord / Voicing Finder render all matching candidates on the virtual fretboard, with compact cards and filters above the SVG acting as selectors/filters instead of showing only one selected candidate.

Completed:
- Chord / Voicing Finder now renders the filtered candidate set onto the SVG fretboard, with the selected candidate emphasized but non-selected candidates still visible.
- Candidate cards now carry matching marker IDs/tones and share the same color system as SVG markers.
- Added compact Chord Finder map filters: All, Open, Pedals, Levers, Low frets, Mid frets, High frets, Complete, Partial, Rootless, Core, Extended, Two-string. Only filters with matches are shown.
- Card filters update both visible cards and SVG markers from the same filtered row set.
- Pedals / levers scope changes reset stale selection and rebuild cards/markers.
- Candidate cards wrap into a compact grid for Chord Finder map mode instead of a long horizontal-only rail.
- Explorer HTML cache-bust was refreshed to `e9-fretboard-explorer.js?v=chord-map-view-20260627`.

Intentionally not changed:
- Backend/music rules, candidate generation, copedent data, notation logic, routing, corpus, Chroma/vector stores, scraping, auth, DNS, deployment config, and raw/design assets.
- Existing Single grip, Harmonized scale path, Single-note finder, Voicing Identifier, glossary, copedent chart, and answer-page behavior.

## Files Changed

- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-1259-06-chord-voicing-finder-map-view.md`

Deleted files: none.
Generated artifacts: none.

## Behavior Notes

Local Chord / Voicing Finder smoke:

```text
Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=chord-map-view-local
- Cache-busted URL tested: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=chord-map-view-local
- Exact URL the user should use: protected-preview URL after commit/protected smoke
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: 8d1b5d8 at start of implementation
- Version endpoint: not checked for local static smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local file state and cache-busted static URL
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: not relevant to this Explorer static smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not relevant
- Who should test this URL: Codex locally; user should test protected-preview URL after Lane 12 smoke
- Do not test these URLs: unversioned Explorer URL for this slice
- Known caveats: static/browser smoke validates the local static UI; protected-preview smoke still needed after commit.
```

Verified locally:
- `F` + `Major` + `All practical` + `All practical` grip vocabulary rendered 24 Chord Finder cards and 13 SVG marker clusters.
- Open filter reduced the map to open candidates only: 8 cards / 8 markers in one local run.
- Pedals / levers scope `Open only` produced only open cards/markers; restoring `All practical` brought back broader marker/card candidates.
- Selecting a card selected the matching SVG marker and updated detail.
- Selecting a non-overlapping SVG marker selected the matching card/marker.
- Changing root from F to D rebuilt cards/markers and cleared stale F marker state.
- No `[object Object]` appeared.
- Browser console had no relevant warnings/errors during local smoke.

Visual risk:
- Same-fret adjacent chord candidates can still physically overlap in the SVG because they share fret/string regions. Cards remain the reliable disambiguation surface, and SVG marker clusters now represent every visible candidate group. A future visual-design slice could add an explicit same-fret pocket popover if user smoke still finds overlap hard to read.

## Tests And Checks

Passed:
- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/e9-fretboard-explorer-data.js`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` -> `24 passed`
- `.venv/bin/python -m pytest tests/test_explorer_musical_red_team.py -q` -> `4 passed`
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` -> `38 passed`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` -> `34 passed`
- `.venv/bin/python -m pytest tests/test_api_contract.py -q` -> `5 passed`
- `git diff --check`

Skipped:
- Full pytest, because this slice touched only the Explorer static UI and focused suites plus API contract covered the requested regression surface.
- Protected-preview smoke, pending commit.

## Integration Notes

- Chord Finder cards and SVG markers now share `data-marker-id` / marker tone semantics.
- `currentRows` for Chord Finder is now the filtered visible set, and `renderFretboard()` receives the same filtered visible set with the selected row first for selected marker emphasis.
- No schema/API/component contract changes were made outside the static Explorer UI.

## Risk Assessment

Risk: medium-low.

Reason:
- The change is scoped to Chord / Voicing Finder rendering and tests.
- It changes how many SVG markers are mounted in Chord Finder mode, which is the requested behavior, but there is a visual-overlap risk when multiple practical voicings share the same fret area.

Rollback:
- Revert the three scoped implementation/test files from this commit.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-1259-06-chord-voicing-finder-map-view.md`

## Files That Must Not Be Staged

- Existing parked dirty/untracked corpus, Chroma/vector, source-inbox, docs, RAG scripts, brand/public assets, raw design assets, and unrelated generated reports shown by `git status --short`.
- `docs/handoffs/task-completions/integration-status.md` unless refreshed in a separate integration-status step after commit/smoke.

## Recommended Next Lane

Lane 01 exact-path commit, then Lane 12 protected-preview smoke for:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=chord-map-view-<commit>
```

## Commit Readiness

Safe to commit.

## Suggested Next Step

After commit, run protected-preview smoke with:

```text
Lane 12: Smoke the Chord / Voicing Finder map view at the cache-busted Explorer URL. Verify F + Major + All practical shows multiple card/marker candidates, filters narrow both cards and markers, card/marker selection syncs, no stale markers after root/scope changes, no [object Object], and console is clean.
```
