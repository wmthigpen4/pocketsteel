# Fretboard Payload Batch Integration

## Task Summary

Reviewed and integrated the fretboard MVP payload batch across Lane 18 Product / Architecture, Lane 05 Backend / RAG Integration, and Lane 15 QA / Answer Eval.

The batch is coherent from product contract to deterministic E9 known-position generation to QA/API-boundary fixtures. The backend emits contract-style `response.fretboard.positions` and preserves legacy `highlights` for the current UI consumer.

## Files Changed

Expected commit files:

- `docs/fretboard-payload-contract.md`
- `pocketsteel/fretboard_examples.py`
- `pocketsteel/api_contract.py`
- `tests/test_fretboard_examples.py`
- `tests/test_api_contract.py`
- `tests/test_api_search.py`
- `tests/fixtures/fretboard_payload_qa_cases.json`
- `tests/test_fretboard_payload_qa.py`
- `docs/handoffs/task-completions/2026-06-11-1615-18-fretboard-payload-contract.md`
- `docs/handoffs/task-completions/2026-06-11-1624-05-e9-known-position-library.md`
- `docs/handoffs/task-completions/2026-06-11-1634-15-fretboard-payload-qa-fixtures.md`
- `docs/handoffs/task-completions/2026-06-11-1637-fretboard-payload-batch-integration.md`

Generated artifacts:

- None staged or committed.

Explicitly out of scope:

- SGF scraping
- `manifest.sqlite`
- corpus data
- embeddings
- Chroma/vector DB
- deployment
- auth/security
- unrelated UI visual redesign

## Tests And Checks

Commands run:

```bash
git status --short
git log --oneline -8
git diff --check
.venv/bin/python -m py_compile pocketsteel/fretboard_examples.py pocketsteel/api_contract.py
.venv/bin/python -m pytest tests/test_fretboard_examples.py tests/test_fretboard_payload_qa.py tests/test_api_contract.py tests/test_api_search.py::test_location_based_g_chord_answer_includes_fretboard_payload tests/test_api_search.py::test_i_iv_v_question_includes_fretboard_payload tests/test_api_search.py::test_common_grips_question_includes_fretboard_payload tests/test_api_search.py::test_non_location_answer_omits_fretboard_payload tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest
```

Results:

- Targeted backend/rules/API/frontend checks: `46 passed`
- Full test suite: `401 passed`
- Working tree diff whitespace check: passed

## Integration Notes

Confirmed MVP facts:

- `g-open-3`: fret `3`, strings `[4, 5, 6]`, pedals `[]`, levers `[]`
- `g-af-6`: fret `6`, strings `[4, 5, 6]`, pedals `["A"]`, levers `["F"]`
- `g-ab-10`: fret `10`, strings `[4, 5, 6]`, pedals `["A", "B"]`, levers `[]`
- A+F and A+B are not swapped.
- Unsupported full-solo tab requests do not emit invented fretboard payloads.

Contract consistency:

- Product contract defines `response.fretboard.positions` as the source-of-truth payload.
- Backend known-position library emits contract fields and validates deterministic payloads.
- Legacy `highlights` remains for existing UI consumption during migration.
- QA fixtures lock the G major MVP facts and forbid raw geometry fields.
- Backend does not emit UI-owned `x`, `y`, `cx`, `cy`, or coordinate fields.

## Risk Assessment

Risk level: Low.

The batch is deterministic, fixture-backed, and keeps existing UI compatibility via `highlights`. The main open product question is whether control-specific prompts like `Show me G major with A+B` should eventually return a single focused position instead of the full G major positions payload.

Rollback path:

```bash
git revert <commit>
```

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 06 UX/UI Design should migrate the answer UI from legacy `highlights` toward contract `positions` when ready, while preserving the current compatibility path until browser-smoked.
