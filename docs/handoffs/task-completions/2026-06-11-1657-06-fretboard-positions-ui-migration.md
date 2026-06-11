# Task Summary

- Requested: migrate the pedal steel fretboard answer UI to treat `response.fretboard.positions` as the primary rendering contract while preserving temporary compatibility with legacy `response.fretboard.highlights`.
- Completed: preserved `positions` in `ui/answer-client.js`, passed `positions` through the answer screen mount path, and updated `ui/pedal-steel-fretboard.js` so a present `positions` array is authoritative. Legacy `highlights` are used only when `positions` is absent.
- Completed: normalized both contract positions and legacy highlights into the existing internal render model, preserving current fret/string geometry and highlight behavior.
- Completed: added position-contract test coverage for A+F at fret 6, A+B at fret 10, strings/grip `4-5-6`, positions-over-highlights precedence, and legacy fallback.
- Intentionally not changed: backend known-position logic, answer generation, corpus pipeline, SGF scraping, `manifest.sqlite`, Chroma/vector stores, deployment, auth/security, decorative SVG design, fret formula, string math, fretboard geometry, marker set, aspect ratio, and the accepted fret-24 pickup gap.

# Files Changed

- Changed files:
  - `ui/pedal-steel-fretboard.js`
  - `ui/answer-client.js`
  - `ui/steel-guitar-rag-mock.html`
  - `tests/test_pedal_steel_fretboard_ui.py`
  - `tests/test_frontend_answer_ui.py`
- Created files:
  - `docs/handoffs/task-completions/2026-06-11-1657-06-fretboard-positions-ui-migration.md`
- Deleted files:
  - None
- Generated artifacts:
  - `/tmp/steel-rag-fretboard-positions-desktop.png`
  - `/tmp/steel-rag-fretboard-legacy-desktop.png`
  - `/tmp/steel-rag-fretboard-positions-mobile-expanded.png`
  - `/tmp/steel-rag-fretboard-positions-smoke-facts.json`
  - `/tmp/steel-rag-fretboard-legacy-smoke-facts.json`
  - `/tmp/steel-rag-fretboard-positions-mobile-facts.json`

# Tests And Checks

- `node --check ui/pedal-steel-fretboard.js`
  - Passed
- `node --check ui/answer-client.js`
  - Passed
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py tests/test_frontend_answer_ui.py -q`
  - Passed: 35 passed
- `git diff --check`
  - Passed

Browser smoke:

- Positions payload URL: `http://127.0.0.1:8792/ui/steel-guitar-rag-mock.html?access=beta_user`
- Legacy payload URL: `http://127.0.0.1:8793/ui/steel-guitar-rag-mock.html?access=beta_user`
- Positions smoke:
  - Rendered title: `Contract positions payload`
  - Rendered contract IDs: `contract-g-open-3`, `contract-g-af-6`, `contract-g-ab-10`
  - Rendered frets: `3`, `6`, `10`
  - Rendered strings: `4,5,6`
  - The intentionally stale `wrong-legacy` highlight did not appear.
  - Legend showed grip, controls, role, intervals, notes, and explanation from the new contract where provided.
- Legacy fallback smoke:
  - Rendered title: `Legacy highlight fallback`
  - Rendered legacy IDs: `legacy-g-open-3`, `legacy-g-af-6`, `legacy-g-ab-10`
  - Rendered frets: `3`, `6`, `10`
  - Rendered strings: `4,5,6`
- Mobile/narrow smoke:
  - Viewport: `390x844`
  - Positions payload rendered in the answer screen after expanding the fretboard details panel.
  - Page width stayed contained at `390px`; fretboard stayed in its internal scroll stage.
- Temporary smoke servers on ports `8792` and `8793` were stopped after testing.

Screenshots:

![Positions payload desktop](/tmp/steel-rag-fretboard-positions-desktop.png)
![Legacy highlights fallback desktop](/tmp/steel-rag-fretboard-legacy-desktop.png)
![Positions payload mobile expanded](/tmp/steel-rag-fretboard-positions-mobile-expanded.png)

# Integration Notes

- Payload normalization happens in two places:
  - `ui/answer-client.js` preserves `fretboard.positions` only when the API actually sends it, and continues preserving legacy `fretboard.highlights`.
  - `ui/pedal-steel-fretboard.js` normalizes either `positions` or `highlights` into one internal render model. If `options.positions` is an array, it is primary. If `options.positions` is absent, legacy `options.highlights` are used.
- The answer screen passes both fields into `mountPedalSteelFretboard()`.
- New contract fields now used by the UI:
  - `id`
  - `label`
  - `fret`
  - `strings`
  - `grip`
  - `pedals`
  - `levers`
  - `notes`
  - `intervals`
  - `explanation`
- The internal model property is still named `highlights` for compatibility with existing rendering and tests, but it may now contain normalized contract positions. Each normalized item carries `sourceType` as `position` or `highlight`.
- No raw backend x/y geometry is required or consumed. Fret positions remain computed by the existing frontend equal-temperament geometry.
- Assumption: if the backend sends `positions: []`, the UI should render no positions even if `highlights` is also present. This follows the requested rule that present `positions` are primary.
- Blockers: none.
- Human decisions needed: decide later when legacy `highlights` compatibility can be removed.

# Risk Assessment

- Risk: Low
- Why: change is isolated to frontend payload normalization/rendering and tests. Backend contract, retrieval, data, and geometry were untouched.
- Compatibility risk: temporary fallback remains, but future payloads with both `positions` and stale `highlights` will ignore `highlights`. This is intended.
- Rollback notes: revert the changes in `normalizeFretboard()`, `renderFretboardVisualization()`, the `positions`/`highlights` selection in `buildFretboardModel()`, and the related tests.

# Commit Readiness

Safe to commit

# Suggested Next Step

- Lane: 05 Backend / RAG Integration
- Recommended prompt: "Run a protected-preview smoke using a real backend `response.fretboard.positions` payload from known-position logic and confirm the frontend renders contract IDs/frets without any smoke-only fixture."
