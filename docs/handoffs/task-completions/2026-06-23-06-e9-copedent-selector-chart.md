# 2026-06-23 06 E9 Copedent Selector Chart

## Task Summary

Lane 06 was asked to add an E9 copedent selector and visual copedent chart to the browser-accessible E9 Fretboard Explorer, using the backend copedent data contract from `86abdaa`.

Completed:

- Added an `E9 setup` selector near the Explorer top controls.
- Exposed `Emmons E9` and `Day E9`.
- Kept `My Copedent (E9)` disabled with visible coming-soon copy: `My Copedent (E9) is coming soon in Backstage.`
- Added a visual copedent chart showing strings 1-10, open notes, pedal/lever columns, physical positions, and raise/lower cell notation.
- Wired the Pedal and Lever Impact Preview to the selected copedent payload.
- Preserved existing key/scale/harmony/string-group filters, selected-position rendering, fretboard rendering, and Explorer route.

Intentionally not changed:

- No backend copedent generation logic.
- No C6 selector or C6 UI.
- No My Copedent editor.
- No auth, DNS, deployment, corpus, Chroma, embeddings, scraping, private data, or asset changes.
- No `integration-status.md` staging.

## Files Changed

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer-data.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-23-06-e9-copedent-selector-chart.md`

Generated screenshot artifacts:

- `docs/handoffs/task-completions/assets/2026-06-23-06-e9-copedent-selector-chart/emmons-chart-viewport.png`
- `docs/handoffs/task-completions/assets/2026-06-23-06-e9-copedent-selector-chart/day-chart-viewport.png`
- `docs/handoffs/task-completions/assets/2026-06-23-06-e9-copedent-selector-chart/my-copedent-disabled-copy-viewport.png`
- `docs/handoffs/task-completions/assets/2026-06-23-06-e9-copedent-selector-chart/impact-preview-viewport.png`

## UI Behavior Added

Selector:

- Default: `Emmons E9`.
- Selectable alternate: `Day E9`.
- Disabled option: `My Copedent (E9) - Coming soon in Backstage`.
- Visible helper copy explains setup selection and coming-soon status.

Copedent chart:

- Shows strings 1-10.
- Shows open notes.
- Shows control columns including pedals and knee levers.
- Shows physical positions such as `P1`, `P2`, `P3`, `LKL`, `LKR`, `LKV`, `RKR`, and `RKL`.
- Shows note movement cells such as `B -> C#`, `E -> F`, `E -> Eb/D#`, `D -> C#`, and raise/lower semitone labels.

Impact preview:

- Re-renders from the selected copedent payload.
- Emmons shows A/B/C ordering.
- Day shows C/B/A ordering while preserving named pedal semantics.
- Lever controls remain visible, including right-knee controls exposed by the backend contract.

## Browser Smoke

Smoke Target:

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?access=beta_user&v=e9-copedent-selector-smoke`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?access=beta_user&v=e9-copedent-selector-smoke`
- Exact URL the user should use: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?access=beta_user&v=e9-copedent-selector-smoke`
- Auth required: no for local
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `86abdaa` plus working tree UI changes before commit
- Version endpoint: not checked for local static UI smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local server served the current working tree
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not relevant to this Explorer-only smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not relevant to this Explorer-only smoke
- Who should test this URL: Codex, then Lane 15/Lane 12 after commit if needed
- Do not test these URLs: production/protected preview in this lane
- Known caveats: local browser smoke does not prove protected-preview cache state

Smoke result:

- PASS: Emmons selected by default and chart visible.
- PASS: Day selectable and chart visible with Day pedal order.
- PASS: `My Copedent (E9)` is disabled and coming-soon copy is visible.
- PASS: Pedal and Lever Impact Preview renders selected copedent controls.
- PASS: No `[object Object]` found in browser-rendered page text during smoke.

Screenshots captured:

- `docs/handoffs/task-completions/assets/2026-06-23-06-e9-copedent-selector-chart/emmons-chart-viewport.png`
- `docs/handoffs/task-completions/assets/2026-06-23-06-e9-copedent-selector-chart/day-chart-viewport.png`
- `docs/handoffs/task-completions/assets/2026-06-23-06-e9-copedent-selector-chart/my-copedent-disabled-copy-viewport.png`
- `docs/handoffs/task-completions/assets/2026-06-23-06-e9-copedent-selector-chart/impact-preview-viewport.png`

## Tests And Checks

Passed:

- `git diff --check`
- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/e9-fretboard-explorer-data.js`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` (`23 passed`)
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` (`34 passed`)
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` (`37 passed`)

## Integration Notes

- The UI consumes `selected_copedent`, `filters.available_copedents`, `control_impact_preview`, and row-level `control_impacts`.
- The static Explorer data file now includes both default Emmons payloads and Day payloads under `window.STEEL_RAG_E9_EXPLORER_PAYLOADS_BY_COPEDENT`.
- `My Copedent (E9)` remains disabled and is not treated as a usable data profile.
- No Explorer row generation logic changed.

## Risk Assessment

Risk: medium.

Reason:

- The UI change is scoped, but `ui/e9-fretboard-explorer-data.js` is a generated static fixture and is large.
- Local smoke passed, but protected-preview cache behavior still needs Lane 12 verification after commit.

Rollback:

- Revert the scoped UI/test commit.
- If only static data is problematic, revert `ui/e9-fretboard-explorer-data.js` and the selector references together.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer-data.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-23-06-e9-copedent-selector-chart.md`

Screenshot artifacts may remain untracked unless Repo Steward wants screenshot evidence committed:

- `docs/handoffs/task-completions/assets/2026-06-23-06-e9-copedent-selector-chart/`

## Files That Must Not Be Staged

- `docs/handoffs/task-completions/integration-status.md`
- `README.md`
- `corpus_metadata/`
- `source-inbox/`
- `rag_*.py`
- `ui/brand/`
- `public/brand/`
- `Neon Sign/`
- any corpus, Chroma/vector, embeddings, scraping, auth, DNS, deployment, private-source, or unrelated dirty files

## Recommended Next Lane

Lane 12 protected-preview restart/smoke after commit, then Lane 15 browser QA for Explorer copedent selector/chart behavior.

## Commit Readiness

Safe to commit if exact-path staged with only the safe-to-stage files above and staged diff checks pass.

## Suggested Next Step

Lane 12: restart/refresh protected preview and smoke `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-copedent-selector-smoke` to verify the committed selector/chart and cache-busted scripts.
