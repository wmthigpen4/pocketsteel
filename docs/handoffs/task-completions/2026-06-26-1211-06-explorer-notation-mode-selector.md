# 2026-06-26 12:11 - Lane 06 - Explorer Notation Mode Selector

## Task Summary

Requested: replace the E9 Fretboard Explorer's binary Notes/Intervals toggle with a four-way notation selector:

- Notes
- NNS
- Roman
- Numbers

Completed: implemented the notation selector in the Explorer UI and wired the active notation mode through scale display, row cards, SVG marker labels, selected detail copy, top-label filters, tooltips, fretboard position payloads, and pedal/lever impact context. The previous binary label-mode UI was removed.

Intentionally not changed: backend Explorer rules, Explorer data generation, fretboard geometry, corpus, Chroma/vector stores, embeddings, scraping, auth, DNS, deployment, protected-preview runtime, and visual assets.

## Files Changed

- `ui/e9-fretboard-explorer.html`
  - Replaced the old Notes/Intervals toggle with `Notes`, `NNS`, `Roman`, and `Numbers`.
  - Updated the scale summary label and glossary language for the new notation modes.
  - Updated the top-label filter aria label.
- `ui/e9-fretboard-explorer.js`
  - Added notation-mode constants and formatting helpers.
  - Defaulted the Explorer to Notes mode.
  - Routed cards, SVG marker labels, detail text, tooltips, selected-detail fields, fretboard positions, top-label filters, scale display, and pedal/lever impact context through the active notation mode.
  - Reset top-label filtering when notation mode changes.
- `tests/test_frontend_answer_ui.py`
  - Updated static Explorer assertions for the four-way notation selector.
  - Updated the VM smoke harness and assertions for Notes, NNS, Roman, and Numbers behavior.
- `docs/handoffs/task-completions/assets/2026-06-26-06-explorer-notation-mode-selector/explorer-notation-mode-local.png`
  - Local browser-smoke screenshot.
- `docs/handoffs/task-completions/2026-06-26-1211-06-explorer-notation-mode-selector.md`
  - This handoff.

## Tests And Checks

Passed:

```bash
node --check ui/e9-fretboard-explorer.js
node --check ui/e9-fretboard-explorer-data.js
node --check ui/answer-client.js
node --check ui/pedal-steel-fretboard.js
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py::test_e9_fretboard_explorer_surface_uses_display_fields_and_validated_data tests/test_frontend_answer_ui.py::test_e9_fretboard_explorer_controls_are_mode_aware -q
.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
git diff --check
```

Local browser smoke:

```text
Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=explorer-notation-mode-local
- Cache-busted URL tested: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=explorer-notation-mode-local
- Exact URL the user should use: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=explorer-notation-mode-local
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: f06d226 at task start
- Version endpoint: not checked for local static UI smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local URL served from current working tree
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: not required for this Explorer-only local smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not required for this Explorer-only local smoke
- Who should test this URL: Codex
- Do not test these URLs: protected-preview or production URLs for this local UI slice
- Known caveats: protected-preview cache-bust/restart was not performed in this Lane 06 implementation slice
```

Browser smoke verified:

- Notes mode shows note-name scale and note-name SVG/card labels.
- NNS mode shows `1 - 2- - 3- - 4 - 5 - 6- - 7°` and updates cards/markers.
- Roman mode shows `I - ii - iii - IV - V - vi - vii°` and updates cards/markers.
- Numbers mode shows `1 - 2m - 3m - 4 - 5 - 6m - 7dim` and updates cards/markers.
- Top-label filter text follows the selected notation mode.
- Selected detail and tooltip language follows the selected notation mode.
- Pedal/lever impact context reports the selected notation mode.
- No `[object Object]` was present.

Screenshot:

- `docs/handoffs/task-completions/assets/2026-06-26-06-explorer-notation-mode-selector/explorer-notation-mode-local.png`

## Integration Notes

- The UI continues to use backend display fields for note spellings in Notes mode.
- NNS/Roman/Numbers mode labels are frontend display transforms over validated interval data; no pitch validation or row identity changed.
- The existing top-label filter is now display-mode aware. It filters by the visible top label for the active notation, and resets to `All` when the notation mode changes.
- The previous binary `data-explorer-label-mode` controls are removed from the Explorer surface.

## Risk Assessment

Risk: Low to medium.

Why: This is a learner-facing UI behavior change, but it is isolated to the Explorer page and covered by focused VM/browser-style frontend tests. Backend deterministic rules and payload generation were not changed.

Rollback: revert the scoped commit touching `ui/e9-fretboard-explorer.html`, `ui/e9-fretboard-explorer.js`, `tests/test_frontend_answer_ui.py`, and this handoff/screenshot.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-26-1211-06-explorer-notation-mode-selector.md`
- `docs/handoffs/task-completions/assets/2026-06-26-06-explorer-notation-mode-selector/explorer-notation-mode-local.png`

## Files That Must Not Be Staged

Do not stage unrelated parked changes or untracked files, including but not limited to:

- `README.md`
- `corpus_metadata/**`
- `docs/handoffs/task-completions/integration-status.md` unless refreshed in a separate Repo Steward step
- `rag_*.py`
- `source-inbox/**`
- `ui/brand/**`
- `public/brand/**`
- `Neon Sign/**`
- corpus/private/generated/vector/deployment/auth artifacts

## Recommended Next Lane

Lane 12 should refresh protected-preview/static cache-busts and run protected-preview smoke against the Explorer URL after this commit.

Suggested prompt:

```text
Lane 12: Run protected-preview smoke for the E9 Fretboard Explorer notation selector. Use a fresh cache-busted Explorer URL and verify Notes, NNS, Roman, and Numbers update cards, SVG markers, selected details, and tooltips without `[object Object]`.
```

## Commit Readiness

Safe to commit.

## Suggested Next Step

Commit the scoped Lane 06 UI/test/handoff files, then run Lane 12 protected-preview smoke.
