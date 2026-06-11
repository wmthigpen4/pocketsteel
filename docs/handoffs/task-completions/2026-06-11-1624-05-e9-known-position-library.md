# Task summary

- What was requested: implement the MVP deterministic E9 known-position library for fretboard payloads using the Lane 18 fretboard payload contract.
- What was completed: updated the backend fretboard helper to emit contract-style `response.fretboard.positions` for known E9 cases while preserving legacy `highlights` for existing consumers. The required G major positions are deterministic and validated:
  - `g-open-3`: fret 3, strings 4-5-6, no pedals/levers
  - `g-af-6`: fret 6, strings 4-5-6, A pedal plus F lever
  - `g-ab-10`: fret 10, strings 4-5-6, A+B pedals
- What was intentionally not changed: no UI fretboard rendering, SVG geometry, scraping, manifest/database files, corpus data, embeddings, Chroma/vector DB, auth/security, deployment, or unrelated RAG logic was touched.

# Files changed

- Changed files:
  - `pocketsteel/fretboard_examples.py`
  - `pocketsteel/api_contract.py`
  - `tests/test_fretboard_examples.py`
  - `tests/test_api_contract.py`
  - `tests/test_api_search.py`
- Created files:
  - `docs/handoffs/task-completions/2026-06-11-1624-05-e9-known-position-library.md`
- Deleted files:
  - None
- Generated artifacts:
  - None

# Tests and checks

- `.venv/bin/python -m py_compile pocketsteel/fretboard_examples.py pocketsteel/api_contract.py`
  - Passed.
- `.venv/bin/python -m pytest tests/test_fretboard_examples.py tests/test_api_contract.py tests/test_api_search.py::test_location_based_g_chord_answer_includes_fretboard_payload tests/test_api_search.py::test_i_iv_v_question_includes_fretboard_payload tests/test_api_search.py::test_common_grips_question_includes_fretboard_payload tests/test_api_search.py::test_non_location_answer_omits_fretboard_payload`
  - Passed: 24 tests.
- `.venv/bin/python -m pytest tests/test_api_search.py tests/test_answer_eval.py`
  - Passed: 141 tests.
- `git diff --check`
  - Passed.
- Tests skipped and why:
  - Full `pytest` was not run because this task touched the deterministic backend/rules payload layer plus answer-payload test contracts, and the targeted backend/API/eval suites covered the changed behavior.

# Integration notes

- Contract docs used:
  - `docs/handoffs/task-completions/2026-06-11-1615-18-fretboard-payload-contract.md`
  - `docs/fretboard-payload-contract.md`
- API/function names added or refined:
  - `get_fretboard_examples(intent, key)`
  - `fretboard_payload_for_question(question)`
  - `get_e9_major_chord_positions(key)`
  - `build_e9_major_chord_fretboard(key)`
  - `validate_fretboard_payload(payload)`
- Contract behavior:
  - New deterministic payloads include `type`, `title`, `subtitle`, `description`, `tuning`, `copedent`, `key`, `strings`, `positions`, `legend`, `notes`, `warnings`, and `sourceContext`.
  - `positions` is the contract source of truth.
  - `highlights` is still emitted as a legacy compatibility projection for current answer/UI consumers.
  - Canonical contract labels are used for new data: pedals `A`, `B`, `C`; levers `F`, `E`, `G+`, `G-`, `D-`, `D--`, `V`.
- Supported known positions:
  - G major MVP positions at frets 3, 6, and 10.
  - Safe deterministic transposition remains available for simple major positions, I-IV-V examples, minor-family examples, and common grips, all bounded by the contract validator.
- Unsupported cases:
  - No full chord engine.
  - No slants.
  - No raw x/y/SVG/pixel geometry.
  - No LLM-generated fretboard locations.
  - Unknown intents and unsupported keys raise `ValueError`; unsupported natural-language trigger questions return no fretboard payload.
- Human decisions needed:
  - Decide when Lane 06 should migrate the UI from reading legacy `highlights` to contract `positions`.

# Risk assessment

- Risk: Low
- Why: changes are deterministic, test-covered, and confined to backend payload generation/types plus tests. Existing consumers keep receiving `highlights`.
- Rollback notes: revert the listed changed files to remove the contract-position emission and return to the previous highlights-only helper.

# Commit readiness

Safe to commit

# Suggested next step

- Lane: 15 QA / Answer Eval
- Recommended prompt: "Add QA fixtures for `response.fretboard.positions` using the G major MVP payload from `pocketsteel/fretboard_examples.py`. Verify `g-open-3`, `g-af-6`, and `g-ab-10` remain stable, no raw geometry fields appear, and existing answer responses without fretboard payloads remain unchanged."
