# 2026-06-18 - Lane 06 - Tab Example Fretboard Rendering

## Task Summary

Requested: render the existing SVG fretboard/card visualization for answer-triggered deterministic tab examples when the backend provides a fretboard payload. The user smoke issue was that "Show me a G major grip" rendered a tab card but did not show the fretboard.

Completed:

- Added frontend normalization support for backend-provided fretboard payloads nested under `tab_example.fretboard` and `tabExample.fretboard`.
- Preserved existing top-level `fretboard` behavior.
- Added focused frontend tests proving:
  - `tab_example` without backend fretboard does not invent fretboard state.
  - `tab_example` with backend fretboard preserves/normalizes the fretboard positions.
  - The rendered answer page can show tab card plus mounted fretboard, then clear both on a following non-tab response.

Intentionally not changed:

- No frontend fake tab generation.
- No frontend fake fretboard generation from tab events.
- No backend routing or tab example selection logic.
- No fretboard geometry, SVG component internals, landing/static/cache-bust work, Chroma, corpus, scraping, auth, deployment, or DNS.
- No event selector or animation.

## Files Changed

- `ui/answer-client.js`
  - `findFretboardPayload(...)` now checks:
    - top-level `payload.fretboard`,
    - nested `payload.tab_example.fretboard`,
    - nested `payload.tabExample.fretboard`,
    - existing nested `response/data/result/answer` shapes.
  - If a nested tab-example fretboard lacks a title/description, the normalizer can use the normalized tab title/explanation as fallback display text.
- `tests/test_frontend_answer_ui.py`
  - Added normalization coverage for `tab_example.fretboard`.
  - Added an assertion that tab-only payloads do not synthesize `fretboard`.
  - Extended the rendered-DOM answer test so a tab card plus fretboard mounts together and both clear on a subsequent non-tab response.
- `docs/handoffs/task-completions/2026-06-18-06-tab-example-fretboard-rendering.md`
  - This handoff.

## Payload Shape Consumed

Supported frontend input shape:

```json
{
  "tab_example": {
    "id": "g-major-456-open",
    "title": "G major 4-5-6 grip",
    "rendered_tab": "...",
    "validation": { "ok": true },
    "explanation": "A compact validated G grip.",
    "fretboard": {
      "title": "G major 4-5-6 grip",
      "description": "Strings 4-5-6 at fret 3.",
      "positions": [
        {
          "id": "g-major-456-open-1",
          "label": "G major",
          "fret": 3,
          "strings": [4, 5, 6],
          "grip": [4, 5, 6]
        }
      ]
    }
  }
}
```

Camel-case compatibility is also supported for `tabExample.fretboard`.

The UI still consumes top-level `fretboard` as before.

## UI Behavior

- If the normalized answer includes `tabs` and `fretboard`, the tab card renders after the main answer and the existing fretboard visualization renders below it.
- The fretboard is still mounted through `window.STEEL_RAG_FRETBOARD.mountPedalSteelFretboard(...)`.
- The frontend does not derive positions from tab text or events. It only renders a backend-provided fretboard payload.
- If no fretboard payload exists, no fretboard area is shown.

## Clearing / Stale-State Behavior

The existing clear paths remain in force:

- loading state clears tab and fretboard,
- error state clears tab and fretboard,
- return-to-stage clears tab and fretboard,
- rendering a subsequent response without fretboard hides and clears the fretboard mount.

The rendered-DOM test now also verifies that a non-tab response after a tab/fretboard response hides the tab card and clears the fretboard.

## Tests And Checks Run

Passed:

- `git diff --check`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q`
  - `20 passed`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q`
  - `29 passed`
- `.venv/bin/python -m pytest tests/test_tab_engine.py -q`
  - `20 passed`

Repo Steward follow-up after backend commit `12eef1d`:

- `.venv/bin/python -m pytest tests/test_api_search.py -q`
  - `257 passed`
- `.venv/bin/python -m pytest tests/test_api_contract.py -q`
  - `5 passed`
- `.venv/bin/python -m py_compile pocketsteel/tab_engine.py pocketsteel/api.py pocketsteel/answer_tab_examples.py`
  - passed
- `.venv/bin/python -m pytest -q`
  - `756 passed, 2 failed`
  - Remaining failures are known unrelated static/UI caveats:
    - `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`
    - `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`

## Limitations

- No protected-preview browser smoke was run in this Repo Steward pass.
- No event selector/toggle was added.
- No animation or tab-to-SVG synchronization was added.
- No frontend inference from `tab_example.events` was added.

## Risks

Risk: Medium-low.

The frontend change is small and now passes the required backend/API and frontend checks after the backend payload commit `12eef1d`. Protected-preview browser smoke still needs to run from the final committed HEAD.

Rollback:

- Revert the small `findFretboardPayload(...)` addition and the related frontend test assertions.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/answer-client.js`
- exact tab-example/fretboard hunks in `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-18-06-tab-example-fretboard-rendering.md`

## Files That Must Not Be Staged

Do not stage unrelated parked work, including:

- `pocketsteel/api.py`
- `pocketsteel/answer_tab_examples.py`
- landing/sign assets and cache-bust changes,
- corpus/source files,
- Chroma/vector data,
- raw design assets,
- deployment/DNS/auth files,
- existing unrelated docs/handoffs.

## Recommended Next Lane

Lane 01 Repo Steward should commit the verified frontend normalization/test slice, then Lane 12 should run current-HEAD protected-preview smoke.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 12: run current-HEAD protected-preview smoke for answer-triggered tab examples and fretboard cards.
