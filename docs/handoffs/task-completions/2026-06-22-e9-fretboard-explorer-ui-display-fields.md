# E9 Fretboard Explorer UI Display Fields

## Task summary

Lane: 06 UX/UI Design
Branch: `feature/answer-api`
Starting HEAD: `c42b236`

Requested: wire the E9 Fretboard Explorer UI to consume backend key-aware learner-facing display fields from commit `c42b236`.

Completed:

- Updated the shared SVG fretboard/card component to prefer Explorer display fields in learner-facing text:
  - `display_notes`
  - `display_top_voice`
  - `display_summary`
  - `query.display_scale_notes`
- Preserved canonical/internal pitch values for backend validation; the UI no longer needs to render canonical `notes` for learner-facing Explorer note lists.
- Passed `fretboard.query` through answer normalization and protected-preview mounting so real answer payloads can reach the component.
- Added focused frontend regression coverage for G natural minor spelling: `G A Bb C D Eb F`, not `G A A# C D D# F`.

Intentionally not changed:

- No backend Explorer generation or pitch validation changes.
- No corpus, Chroma/vector DB, embeddings, scraper output, deployment, auth, DNS, assets, private source data, or raw design files touched.
- No broad product rename.

## Files changed

- `ui/pedal-steel-fretboard.js`
- `ui/answer-client.js`
- `ui/steel-guitar-rag-mock.html`
- `tests/test_pedal_steel_fretboard_ui.py`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-ui-display-fields.md`

## UI fields wired

- `display_notes`: normalized into the learner-facing Notes card/detail/legend content before falling back to canonical `notes`.
- `display_top_voice`: rendered as the learner-facing Top voice detail before falling back to canonical `top_voice`.
- `display_summary`: rendered in selector card text and the Short explanation detail before falling back to legacy explanation fields.
- `query.display_scale_notes`: rendered in a compact scale strip above position cards and passed through from `answer-client.js` and `ui/steel-guitar-rag-mock.html`.

## Validation performed

Focused UI regression verifies:

- G natural minor scale display renders `G A Bb C D Eb F`.
- Canonical sharp spelling sequence `G A A# C D D# F` is not rendered as the learner-facing scale.
- Row cards/details render `display_notes` (`Bb`, `Eb`) instead of canonical `A#`, `D#`.
- Top voice renders `display_top_voice`.
- Summary renders `display_summary`.
- E9 mechanical spelling remains allowed and visible through per-string changes, including `Eb/D#`.
- Core grip `4-5-6` remains separate from advanced swap / E-lower pocket grip `5-7-8`.
- Partial/advanced warnings remain visible.
- The component does not render `[object Object]`.
- The UI does not say or imply that RAG generated the Explorer positions.

## Tests and checks

Passed:

- `node --check ui/pedal-steel-fretboard.js`
- `node --check ui/answer-client.js`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q`
  - `30 passed`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q`
  - `20 passed`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py tests/test_frontend_answer_ui.py -q`
  - `50 passed`
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q`
  - `11 passed`
- `.venv/bin/python -m pytest -q`
  - `787 passed`
- `git diff --check`
  - passed

Pending after this handoff:

- exact-path staged diff review
- scoped commit

## Integration notes

- The shared component now understands Explorer-style payload fields without requiring a separate Explorer route.
- `answer-client.js` now preserves `fretboard.query` when normalizing a supported fretboard payload.
- The protected-preview inline render path passes `query` through to `mountPedalSteelFretboard`.
- Existing answer-position payloads continue to work through the same fallback paths.

## Risk assessment

Risk: low to medium.

Reason:

- The change touches shared fretboard rendering, but it is additive and fallback-based.
- Full pytest passed.
- Main remaining risk is visual density if an Explorer payload renders many scale/position rows at once; the component already has filtering and horizontal scroll behavior.

Rollback:

- Revert the scoped commit containing the five UI/test files and this handoff.

## Human decision needed

No.

## Safe-to-stage exact file list

- `ui/pedal-steel-fretboard.js`
- `ui/answer-client.js`
- `ui/steel-guitar-rag-mock.html`
- `tests/test_pedal_steel_fretboard_ui.py`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-ui-display-fields.md`

## Files that must not be staged

- Any unrelated dirty files shown by `git status --short`.
- Protected or unrelated paths including `corpus-private/`, `corpus-v2/`, `source-inbox/`, Chroma/vector stores, embeddings, scraper outputs, deployment/auth/DNS config, `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, and generated reports.

## Recommended next lane

Lane 15 QA / Answer Eval.

Suggested next prompt:

```text
Lane 15: QA-smoke the E9 Fretboard Explorer UI display spelling. Verify G natural minor renders Bb/Eb learner-facing spellings, canonical pitch validation remains unchanged, 5-7-8 remains advanced/E-lower, warnings and per-string changes remain visible, and non-Explorer fretboard answers still render normally.
```

## Commit readiness

Safe to commit.
