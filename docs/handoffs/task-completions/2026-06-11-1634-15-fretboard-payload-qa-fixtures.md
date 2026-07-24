# Task summary

- What was requested: add Lane 15 QA/eval coverage proving that MVP E9 `response.fretboard` payloads remain correct and stable, using the Lane 18 fretboard payload contract and Lane 05 deterministic E9 known-position library.
- What was completed: added a stable JSON QA fixture for the required G major known-position cases and a deterministic API-boundary test module that validates supported questions emit contract-shaped fretboard payloads. The tests lock the prior A+F/A+B swap regression and verify unsupported full-solo tab requests do not emit invented fretboard payloads.
- What was intentionally not changed: no UI rendering, no `ui/pedal-steel-fretboard.js`, no fretboard SVG geometry, no SGF scraping, no `manifest.sqlite`, no corpus data, no embeddings, no Chroma/vector DB, no auth/security, no deployment, and no unrelated product docs were touched.

# Files changed

- Changed files:
  - `steel_guitar_rag/fretboard_examples.py`
- Created files:
  - `tests/fixtures/fretboard_payload_qa_cases.json`
  - `tests/test_fretboard_payload_qa.py`
  - `docs/handoffs/task-completions/2026-06-11-1634-15-fretboard-payload-qa-fixtures.md`
- Deleted files:
  - None
- Generated artifacts:
  - None

# Tests and checks

- `.venv/bin/python -m pytest tests/test_fretboard_payload_qa.py tests/test_fretboard_examples.py tests/test_api_contract.py::test_optional_fretboard_payload_contract_shape tests/test_api_search.py::test_location_based_g_chord_answer_includes_fretboard_payload tests/test_api_search.py::test_non_location_answer_omits_fretboard_payload`
  - Passed: 23 tests.
- `git diff --check`
  - Passed.
- Tests skipped and why:
  - Full `pytest` was not run because this Lane 15 task only added deterministic fixture/API payload QA coverage plus two exact known-position trigger phrases. The targeted QA, known-position, API contract, and existing API payload tests cover the changed behavior.

# Integration notes

- Fixtures added:
  - `g-major-positions`: `Where can I play a G chord?`
  - `g-major-ab`: `Show me G major with A+B.`
  - `g-major-af`: `Show me G major with A+F.`
  - `unsupported-full-solo-tab`: `Generate a full solo tab across every string`
- Tests added:
  - Fixture stability test.
  - Supported-question API response test for `response.fretboard`.
  - Prior swapped-bug regression test for `g-af-6` and `g-ab-10`.
  - Unsupported-query safe-fallback test.
- Facts locked:
  - `g-open-3`: fret `3`, strings `[4, 5, 6]`, pedals `[]`, levers `[]`.
  - `g-af-6`: fret `6`, strings `[4, 5, 6]`, pedals `["A"]`, levers `["F"]`.
  - `g-ab-10`: fret `10`, strings `[4, 5, 6]`, pedals `["A", "B"]`, levers `[]`.
  - A+B must not appear at fret `6`.
  - A+F must not appear at fret `10`.
- Payload contract assertions:
  - `response.fretboard` exists for supported known-position questions.
  - Required top-level fields are present.
  - Position IDs are stable.
  - Frets are within `0-24`.
  - Strings are within `1-10`.
  - No raw `x`, `y`, `cx`, `cy`, or coordinate fields are present.
  - Marker frets are not required in the backend payload.
  - Unsupported full-solo tab requests do not emit an invented arbitrary fret/string map.
- Schema/API/component/data contract changes:
  - No schema change.
  - `steel_guitar_rag/fretboard_examples.py` now treats the exact phrases `Show me G major with A+B.` and `Show me G major with A+F.` as deterministic G major known-position triggers so the QA cases validate the API response boundary, not just the helper function.
- Assumptions:
  - The Lane 05 known-position library remains the source of truth for MVP E9 facts.
  - It is acceptable for the control-specific G prompts to return the full G major positions payload, as the fixture requires inclusion/exclusion of the relevant position facts rather than single-position-only output.
- Blockers:
  - None for this QA coverage.
- Human decisions needed:
  - Decide whether future UX should narrow control-specific prompts to a single highlighted position or continue showing all common G major locations.

# Risk assessment

- Risk: Low
- Why: the change is deterministic, fixture-backed, local-test-only except for two exact known-position phrases that now receive the existing G major fretboard payload. It does not touch retrieval, answer quality logic, UI rendering, scraping, corpus data, Chroma, auth, or deployment.
- Rollback notes: remove `tests/fixtures/fretboard_payload_qa_cases.json` and `tests/test_fretboard_payload_qa.py`, and remove the two added exact phrases from `fretboard_payload_for_question()`.

# Commit readiness

Needs human review first

# Suggested next step

- Lane: 05 Backend / RAG Integration
- Recommended prompt: "Review the Lane 15 fretboard payload QA fixtures and decide whether control-specific prompts like `Show me G major with A+B` should return the full G major positions payload or a single-position focused payload. If single-position output is desired, implement it deterministically in `steel_guitar_rag/fretboard_examples.py` without touching UI rendering, corpus data, Chroma, embeddings, scraping, auth, or deployment, then update the Lane 15 fixture expectations."
