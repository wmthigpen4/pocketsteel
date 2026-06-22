# E9 Fretboard Explorer Browser Surface

## Task Summary

Lane: 06 UX/UI Design

Requested: add the first real browser-accessible E9 Fretboard Explorer surface so Lane 15 can run browser smoke against an exact URL.

Completed:
- Added a minimal same-origin Explorer browser page at `ui/e9-fretboard-explorer.html`.
- Added a static browser data fixture generated from `pocketsteel.fretboard_explorer.build_g_explorer_payload()`.
- Added a small Explorer controller that filters validated rows and mounts the existing SVG fretboard renderer.
- Added a landing/app mock entry link: `Explore the E9 Fretboard`.
- Added focused frontend and component tests.
- Preserved canonical backend validation and did not touch corpus, Chroma, embeddings, scraper output, auth, DNS, deployment, assets, or private source data.

Intentionally not changed:
- No backend route or schema changes.
- No corpus/RAG/retrieval behavior changes.
- No deployment or protected-preview restart.
- No visual asset changes.

## Exact Browser Surface

Protected-preview path for Lane 15 smoke:

`https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-browser-surface-20260622`

Local static smoke URL used:

`http://127.0.0.1:8896/ui/e9-fretboard-explorer.html`

## Files Changed

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer-data.js`
- `ui/pedal-steel-fretboard.js`
- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `tests/test_pedal_steel_fretboard_ui.py`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-browser-surface.md`

Generated artifacts:
- `ui/e9-fretboard-explorer-data.js` generated from the validated backend Explorer payload builder.

Deleted files:
- None.

## What Changed

Explorer page:
- Provides key selector with current G-only scope.
- Provides scale selector for G major and G natural minor.
- Provides harmony/view selector for 2-string harmonized scale and 3-string diatonic harmony.
- Provides string-group filter with Core grips, Advanced swaps, and 2-string pairs.
- Uses `query.display_scale_notes` for learner-facing scale spelling.
- Uses `display_notes`, `display_top_voice`, and `display_summary` in row details.
- Shows fret, string group, pedals/levers, per-string changes, warnings, and `pitch_validated`.
- Labels data as validated deterministic Explorer data, not corpus/RAG output.

Fretboard renderer:
- Added `hideFilterControls: true` option so the Explorer surface can use its own controls while still using the existing SVG geometry and card rendering.
- Default renderer behavior remains unchanged when this option is not passed.

Landing entry:
- Added `Explore the E9 Fretboard` link from the protected preview/app mock landing area.

## Explorer Surface Behavior

- G natural minor scale display uses `G A Bb C D Eb F`.
- Canonical/internal pitch values are not used as learner-facing scale display.
- E9 mechanical/copedent note spellings are preserved in the underlying row data where appropriate.
- Core grips and advanced swaps are separated in the string-group selector.
- `5-7-8` appears under Advanced swaps and is rendered as an advanced E-lower pocket.
- Partial warning rows remain visible in the row details.
- Per-string pedal/lever changes remain visible.
- The UI does not claim RAG generated the deterministic Explorer rows.
- The new controller escapes rendered row text and checks for unsafe `[object Object]` output.

## Tests And Checks

Commands run:

```bash
git status --short
git branch --show-current
node --check ui/e9-fretboard-explorer.js
node --check ui/pedal-steel-fretboard.js
node --check ui/answer-client.js
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
.venv/bin/python -m pytest -q
git diff --check
```

Results:
- `node --check ui/e9-fretboard-explorer.js`: passed.
- `node --check ui/pedal-steel-fretboard.js`: passed.
- `node --check ui/answer-client.js`: passed.
- `tests/test_pedal_steel_fretboard_ui.py`: 31 passed.
- `tests/test_frontend_answer_ui.py`: 22 passed.
- `tests/test_fretboard_explorer.py`: 11 passed.
- Full pytest: 790 passed.
- `git diff --check`: passed.

Local static smoke:

```text
/ui/e9-fretboard-explorer.html -> 200 text/html
/ui/e9-fretboard-explorer.js -> 200 text/javascript
/ui/e9-fretboard-explorer-data.js -> 200 text/javascript
/ui/pedal-steel-fretboard.js -> 200 text/javascript
/ui/steel-guitar-rag-mock.html -> 200 text/html
```

Browser smoke:
- Not run against protected preview in this lane. This task created the browser-accessible URL for Lane 15.

## Integration Notes

- The Explorer page is static and same-origin under `/ui/`; no backend route was added.
- The data fixture is generated from the validated backend builder and should be refreshed if the backend payload shape changes.
- Lane 15 should smoke the exact protected-preview URL above after the protected preview runtime includes these files.
- Lane 12 may need to restart/provide the protected preview if the running app is not serving the latest working tree.

## Risk Assessment

Risk: Low to medium.

Why:
- Low backend risk: no backend files changed.
- Low data-contract risk: UI consumes already validated display fields.
- Medium UI risk: this is a new browser page and needs real protected-preview browser smoke before user-facing signoff.

Rollback notes:
- Remove the three new `ui/e9-fretboard-explorer*` files, remove the landing link/CSS from `ui/steel-guitar-rag-mock.html`, and remove the associated tests.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer-data.js`
- `ui/pedal-steel-fretboard.js`
- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `tests/test_pedal_steel_fretboard_ui.py`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-browser-surface.md`

## Files That Must Not Be Staged

Do not stage unrelated dirty or untracked files shown by `git status --short`, especially:
- Corpus/private/source-inbox/provenance files.
- Chroma/vector/embedding outputs.
- Deployment/DNS/auth/secrets files.
- Visual/raw asset directories such as `public/`, `ui/brand/`, and `Neon Sign/`.
- Existing unrelated modified docs/scripts/reports.

## Recommended Next Lane

Lane 15 QA / Answer Eval.

Suggested prompt:

```text
Lane 15: Browser-smoke the E9 Fretboard Explorer surface at https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-browser-surface-20260622. Verify G major and G natural minor display spelling, core/advanced grip separation, 5-7-8 advanced E-lower pocket placement, partial warnings, per-string changes, no [object Object], and that the page labels rows as validated Explorer data rather than RAG output.
```

## Commit Readiness

Safe to commit.

## Suggested Next Step

Commit this scoped UI/browser-surface slice with exact-path staging, then run Lane 15 protected-preview browser smoke against the exact URL above.
