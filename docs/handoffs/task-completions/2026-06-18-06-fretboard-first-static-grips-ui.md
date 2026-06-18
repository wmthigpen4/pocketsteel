# 2026-06-18 06 Fretboard-First Static Grips UI

## Task Summary

Lane: 06 UX/UI Design

Branch: `feature/answer-api`

Starting HEAD: `0006905`

Requested: verify and, if needed, update the answer UI after backend commit `0006905 fix: prefer fretboard for static grip examples`.

Completed:

- Confirmed the existing UI already supports top-level `fretboard` payloads with no tab payload.
- Added a narrow frontend normalization guard so `tab_example` payloads marked `display_tab: false`, `displayTab: false`, or `preferred_display: "fretboard_only"` do not render a visible tab card.
- Added focused regression coverage for static fretboard-only grip answers, movement tab + fretboard answers, and stale-state clearing between response types.

Intentionally not changed:

- No backend answer routing, tab engine logic, Chroma/vector data, embeddings, scraping, corpus data, deployment, DNS, landing/sign work, or answer-page redesign.
- No frontend-inferred fretboard positions or fake tab generation.

## Files Changed

- `ui/answer-client.js`
  - Added `shouldDisplayTabPayload()` and applied it inside `normalizeTabPayload()`.
- `tests/test_frontend_answer_ui.py`
  - Added VM normalization coverage for `display_tab: false` / `preferred_display: "fretboard_only"`.
  - Added rendered-response coverage proving a static fretboard-only answer clears a prior movement tab while keeping the fretboard visible.

Generated artifacts: none.

Deleted files: none.

## UI Behavior

Static grip behavior:

- A response with top-level `fretboard` and no visible tab renders the fretboard section.
- A `tab_example` marked `display_tab: false` or `preferred_display: "fretboard_only"` is normalized away from `tabs`, so no tab card appears.

Movement tab behavior:

- A response with visible tab data plus `fretboard` still renders both the tab card and fretboard.
- Existing tab whitespace preservation remains covered by the frontend tests.

Stale-state behavior:

- Rendering a static fretboard-only response after a movement response hides/clears the previous tab card and mounts the new fretboard payload.
- Rendering a non-tab/non-fretboard response after either answer type hides/clears both tab and fretboard sections.

## Tests And Checks

Passed:

```bash
node --check ui/answer-client.js
node --check ui/pedal-steel-fretboard.js
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
.venv/bin/python -m pytest tests/test_tab_engine.py -q
.venv/bin/python -m pytest tests/test_api_search.py -q
git diff --check
```

Results:

- `tests/test_frontend_answer_ui.py`: 20 passed
- `tests/test_pedal_steel_fretboard_ui.py`: 29 passed
- `tests/test_tab_engine.py`: 23 passed
- `tests/test_api_search.py`: 259 passed

Skipped:

- Browser smoke was not run in this UI slice. Lane 12 should verify protected-preview behavior with the prompt set below.

## Integration Notes

The UI now treats backend display intent as authoritative for deterministic tab examples:

- `display_tab: false`
- `displayTab: false`
- `preferred_display: "fretboard_only"`

These suppress the tab card even when a `rendered_tab` string is present in metadata.

Lane 12 smoke recommendation:

- Static grip prompts should show direct prose + fretboard and no tab card:
  - `Show me a G major grip`
  - `Show me a 4-5-6 grip`
  - `Show me a G chord on strings 4-5-6`
  - `Where is G on E9?`
- Movement prompts should show direct prose + fretboard + tab card:
  - `Show me a G to C move`
  - `How do I use A+B pedals?`
  - `Give me a beginner lick in G`
- Non-tab/copyright/transcription prompts should show no generated tab and no generated fretboard example.

## Risk Assessment

Risk: low.

Why:

- Change is limited to tab payload normalization and focused frontend tests.
- Existing top-level fretboard and tab + fretboard render paths are preserved.
- No backend, schema, routing, retrieval, corpus, deployment, or visual asset changes.

Rollback:

- Revert `shouldDisplayTabPayload()` and the associated test additions.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/answer-client.js`
- `docs/handoffs/task-completions/2026-06-18-06-fretboard-first-static-grips-ui.md`
- `tests/test_frontend_answer_ui.py` exact hunks only:
  - static fretboard-only DOM response hunk around the rendered tab/fretboard test
  - `display_tab: false` / `preferred_display: "fretboard_only"` normalization hunk

## Files That Must Not Be Staged

- The unrelated landing-sign cache-bust hunk in `tests/test_frontend_answer_ui.py`.
- Existing unrelated dirty/parked files shown by `git status --short`, including landing/static assets, corpus/source/provenance files, generated docs/reports, `ui/steel-guitar-rag-mock.html`, and visual assets.
- Any `corpus-private/`, `corpus-v2/`, Chroma/vector store, embeddings, source-inbox raw data, scraping outputs, deployment secrets, `.wrangler/`, DNS config, or raw design assets.

## Recommended Next Lane

Lane 12 Self-Hosted Deployment / Protected Preview smoke.

## Commit Readiness

Safe to commit, if exact-path/hunk staging excludes the unrelated landing-sign cache-bust hunk.

## Suggested Next Step

Lane 12: smoke the protected preview for static grip and movement tab prompts, confirming static grip answers show fretboard-only while movement examples still show tab + fretboard.
