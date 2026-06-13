## Task summary
- What was requested: show why each fretboard position is common, advanced, partial, or useful by rendering new pitch-engine explanation fields in selector cards and detail panels.
- What was completed: `ui/pedal-steel-fretboard.js` now preserves optional `tierReason`, `whenToUse`, `soundCharacter`, `movementUse`, `resolutionUse`, `explanationShort`, `explanationLong`, and `forumEvidenceStatus` fields. Selector cards now include a compact reason such as `starter: straight-bar reference`, `dominant pocket: resolves to I`, or `advanced: partial E-lower color`. Detail panels now include `Why classified`, `When to use`, `What is omitted`, and `Forum usage evidence`, plus optional sound/movement/resolution/extended explanation fields.
- What was intentionally not changed: no backend/RAG routing, answer generation, Chroma, embeddings, corpus, scraping, deployment, auth/security, fret math, string math, marker placement, colors, or tab/filter behavior was changed.

## Files changed
- Changed files:
  - `ui/pedal-steel-fretboard.js`
  - `tests/test_pedal_steel_fretboard_ui.py`
- Created files:
  - `docs/handoffs/task-completions/2026-06-12-2147-06-fretboard-position-reasons.md`
- Deleted files: none
- Generated artifacts: none

## Tests and checks
- `node --check ui/pedal-steel-fretboard.js` - passed
- `node --check ui/answer-client.js` - passed
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` - passed after test expectation correction
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py tests/test_frontend_answer_ui.py tests/test_same_origin_smoke_server.py` - passed, 53 passed
- `git diff --check` - passed
- `.venv/bin/python -m pytest` - failed, 498 passed / 1 failed
  - Failure: `tests/test_api_search.py::test_e_lower_5_7_8_question_uses_pitch_math_not_sources`
  - Failure reason: backend/API answer text no longer contains expected phrase `rootless B minor 7 color`.
  - This was not changed in this Lane 06 task and was left untouched because backend/RAG answer behavior is out of scope.
- Browser smoke: not run for this task; the request did not require it and the UI behavior is covered by component/answer UI tests.

## Integration notes
- New optional backend fields are consumed if present:
  - `tierReason`
  - `whenToUse`
  - `soundCharacter`
  - `movementUse`
  - `resolutionUse`
  - `explanationShort`
  - `explanationLong`
  - `forumEvidenceStatus`
- Snake_case aliases are also accepted for those fields.
- Existing fallback behavior remains:
  - starter positions can show `starter: straight-bar reference`
  - dominant positions can show `dominant pocket: resolves to I`
  - E-lower/advanced positions can show `advanced: partial E-lower color`
  - object maps are formatted as key/value summaries, never as `[object Object]`
- Schema/API contract changes: none. This is a frontend consumer-only change.
- Assumptions: current `formatDetailValue()` behavior is acceptable for nested objects and prefers common user-facing keys such as `note`, `value`, `summary`, and `label`.
- Blockers: full-suite commit gate is blocked by the unrelated backend/API search assertion noted above.
- Human decisions needed: decide whether Lane 05 should restore/update the `rootless B minor 7 color` expectation before commit gate proceeds.

## Risk assessment
- Risk: Low for frontend behavior; the change is additive and scoped to fretboard position metadata display.
- Why: existing rendering paths, tabs, color roles, geometry, and selector/highlight matching were preserved. The new values use the existing safe formatter and HTML escaping.
- Rollback notes: revert `ui/pedal-steel-fretboard.js` and the corresponding assertions in `tests/test_pedal_steel_fretboard_ui.py`.

## Commit readiness
Needs human review first

## Suggested next step
- Lane 05 Backend / RAG Integration should inspect the failing full-suite assertion:
  - `.venv/bin/python -m pytest tests/test_api_search.py::test_e_lower_5_7_8_question_uses_pitch_math_not_sources -vv`
  - Decide whether the answer should again mention `rootless B minor 7 color` or whether the test expectation should be updated to the new deterministic E-lower answer wording.
