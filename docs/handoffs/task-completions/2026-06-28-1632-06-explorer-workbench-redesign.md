# 2026-06-28 16:32 - Lane 06 Explorer Workbench Redesign

## Task Summary
- Requested: redesign the E9 Fretboard Explorer into a premium musical workbench using the provided mockup direction.
- Completed: added visible top-level mode tabs, widened the Explorer shell, restructured the page into a command area, fretboard-centered workbench, result cards below the fretboard, and a right-side "Why this works" inspector.
- Intentionally not changed: backend music rules, Explorer data rows, fretboard geometry, corpus, Chroma/vector stores, scraping, auth, DNS, deployment policy, and visual assets.

## Files Changed
- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-28-1632-06-explorer-workbench-redesign.md`

## UI Behavior Changed
- The five Explorer modes are now visible top-level controls:
  - Single Grip
  - Harmonized Scale Path
  - Single-Note Finder
  - Voicing Identifier
  - Chord / Voicing Finder
- The existing mode `<select>` remains in the DOM as an accessible/state proxy, but it is visually hidden.
- Clicking a mode tab updates the hidden select and runs the existing `updateControls()` / `render()` path.
- The fretboard stage is now the center anchor of the page.
- Active result cards render below the fretboard instead of above it.
- Selected-row teaching detail now lives in a persistent right-side inspector labeled "Why this works".
- The pedal/lever impact section remains below the fretboard workbench.

## Tests And Checks
- `node --check ui/e9-fretboard-explorer.js` - passed
- `node --check ui/answer-client.js` - passed
- `node --check ui/pedal-steel-fretboard.js` - passed
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - 24 passed
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` - 37 passed
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` - 43 passed
- `git diff --check` - passed

## Browser Smoke
Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=explorer-workbench-redesign-local`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=explorer-workbench-redesign-local`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-workbench-redesign-d8ebad9`
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `f521b6c` at task start
- Version endpoint: not checked for local static smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local worktree and cache-busted static URL
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: not relevant to this Explorer route smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not relevant to this Explorer route smoke
- Who should test this URL: Codex locally; user after protected-preview smoke
- Do not test these URLs: uncache-busted Explorer URLs for this change
- Known caveats: local browser smoke does not prove protected-preview freshness

Local browser smoke result:
- Page loaded at the cache-busted Explorer URL.
- Five mode tabs rendered and `Single Grip` was selected by default.
- Fretboard SVG mounted.
- Workbench, stage panel, active result cards, and right-side inspector rendered.
- Active result cards appeared below the fretboard.
- Clicking `Chord / Voicing Finder` updated the selected tab, hidden select state, and visible mode panel.
- Narrow viewport smoke showed no page-level horizontal overflow; workbench collapsed to one column and inspector became static.
- No `[object Object]` appeared.

Protected-preview browser smoke result:
- Protected URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-workbench-redesign-d8ebad9`
- Cloudflare Access result: already authenticated in the in-app browser; no Access login screen shown.
- Browser behavior: page loaded, five mode tabs rendered, default `Single Grip` tab selected, SVG fretboard mounted, workbench and right-side inspector rendered, active results appeared below the fretboard, no page-level horizontal overflow, and no `[object Object]`.
- Root behavior: `https://app.steelguitarrag.com/` redirected to `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`.
- Version endpoint: `https://app.steelguitarrag.com/api/version` returned runtime SHA `a6abc61`, branch `feature/answer-api`, auth provider `cloudflare_access`.
- Caveat: protected preview verified cache-busted static/browser behavior for this Explorer UI change, but the backend runtime SHA is older than implementation commit `d8ebad9`; Lane 12 should restart or otherwise refresh runtime before strict runtime certification.

## Risk Assessment
- Risk: medium. This is a broad layout restructuring of the Explorer surface, but the data contract and music/rendering logic are intentionally preserved.
- Rollback: revert the scoped HTML/JS/test changes from this slice.

## Human Decision Needed
- No for the implemented slice.
- Yes for future visual/product refinements after user smoke, especially if the right-side inspector needs different content hierarchy.

## Safe-To-Stage Exact File List
- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-28-1632-06-explorer-workbench-redesign.md`

## Files That Must Not Be Staged
- Existing unrelated dirty files, including `README.md`, corpus metadata docs/registry files, RAG pipeline files, `source-inbox/inventory.json`, brand assets, raw/generated source assets, corpus/private data, Chroma/vector stores, embeddings, auth/DNS/deployment files, and untracked generated/private files.
- `docs/handoffs/task-completions/integration-status.md` unless refreshed in a separate Repo Steward status step.

## Recommended Next Lane
- Lane 12 protected-preview restart/version alignment if strict runtime certification is required.
- Lane 15 focused QA/user smoke on the new workbench layout.

## Commit Readiness
Safe to commit.

## Suggested Next Step
Lane 15: run focused QA/user smoke against `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-workbench-redesign-d8ebad9`, then Lane 12 can refresh runtime if strict `/api/version` alignment is needed.
