# Retrieval Gating Implementation

Date: 2026-06-13
Branch: feature/answer-api
HEAD: 5844f4e `backend: hook no-op answer intent classifier`

## Summary

Implemented the narrow `/api/answer` retrieval-gating slice approved by QA.

The committed `classify_answer_request(...)` hook now prevents retrieval for:

- `domain == "unsafe_or_impossible"`
- explicit off-domain `small_talk` guardrails: `domain == "off_domain"` and `intent == "small_talk"`

The implementation intentionally does **not** gate all `off_domain/unknown` classifier results because the current classifier uses that as a conservative default for ambiguous prompts. Gating that default broke existing steel-guitar behavior such as `cabinet drop compensator`, practice prompts, invalid chord guardrails, and curated teaching answers. This is the smallest safe runtime gate that blocks the QA-approved off-domain/unsafe classes without broad answer-routing drift.

## Files Changed

- `steel_guitar_rag/api.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/retrieval-gating-implementation.md`

Note: `tests/test_api_search.py` already had broad uncommitted edits from earlier lanes. Repo Steward should review/stage exact hunks for this slice rather than blindly staging the whole file.

## Exact Gating Behavior Implemented

In `steel_guitar_rag/api.py`:

- Added `_answer_intent_guardrail_answer(...)`.
- Added `_should_gate_answer_intent(...)`.
- Renamed the no-op local classifier result to `answer_intent_decision`.
- Added a pre-retrieval branch immediately after request parsing and classification.

Runtime branch:

- If `_should_gate_answer_intent(answer_intent_decision)` returns true, `/api/answer` returns before:
  - deterministic fretboard routes
  - practical curated routes
  - `_search_for_answer(...)`
  - source-card construction
  - fretboard payload attachment

Guardrail response shape:

```json
{
  "answer": "...",
  "mode": "ask",
  "sources": [],
  "warnings": [],
  "sections": [...]
}
```

No classifier metadata is exposed in public JSON.

## Where Retrieval Is Now Skipped

Retrieval is skipped in `RetrievalApi.__call__` before `_search_for_answer(...)`.

Relevant implementation:

- `steel_guitar_rag/api.py:87` adds guardrail answer copy.
- `steel_guitar_rag/api.py:101` adds gate predicate.
- `steel_guitar_rag/api.py:220` calls `classify_answer_request(...)`.
- `steel_guitar_rag/api.py:222` returns a guardrail payload before search when the predicate passes.

## Source Cards And Fretboard Suppression

Guardrail answers always return:

- `sources: []`
- `warnings: []`
- no `fretboard`

Because the response returns before source-card construction, no SGF source cards or source excerpts can be attached to off-domain/unsafe guardrail responses.

Because the response returns before `fretboard_payload_for_question(...)`, no fretboard payload can be attached to off-domain/unsafe guardrail responses.

## Valid Steel Retrieval Still Works

New tests prove these source-backed steel prompts still call retrieval and do not receive fretboard payloads:

- `What are common uses for the E9 9th string?`
- `Who was Buddy Emmons?`
- `Is Mullen or MSA a better guitar?`
- `What vendors sell pedal steel accessories?`

Existing source-backed tests also remained green.

## Fretboard Behavior

The implementation does not add a new fretboard route or change fretboard payload shape.

New tests prove deterministic position prompts can still return fretboard payloads:

- `Where can I play a G chord?`
- `Where can I play a C chord?`

Non-position source-backed steel prompts in the new retrieval-preservation test assert no top-level `fretboard`.

## Teacher-First Composer Scope

Teacher-first answer composer work was not mixed into this slice.

This change only blocks retrieval for approved guardrail domains. It does not change:

- answer-provider synthesis
- source-card rendering
- source-note hierarchy
- teacher-first answer templates
- UI layout
- fretboard rendering
- retrieval ranking

## Tests Added Or Updated

Added focused API tests in `tests/test_api_search.py`:

- `test_classifier_gates_unsafe_prompt_before_retrieval`
- `test_classifier_gates_off_domain_prompt_before_retrieval`
- `test_classifier_gate_preserves_source_backed_steel_retrieval`
- `test_position_questions_can_still_return_fretboard_payloads`

The existing `test_scope_guardrail_for_numbers_prompt_runs_before_retrieval` now exercises the classifier-gated path for large-output prompts because the branch runs before `intent_mode_curated_answer(...)`.

## Tests Run And Results

```bash
git status --short
git diff --check
.venv/bin/python -m pytest tests/test_api_search.py -k "classifier_gate or scope_guardrail_for_numbers or position_questions_can_still or api_answer_returns_frontend_contract or deterministic_mode_specific_sections_render"
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py
.venv/bin/python -m pytest tests/test_answer_eval.py
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py
.venv/bin/python - <<'PY'
# 264-row question-bank classifier validation
PY
.venv/bin/python -m pytest
git diff --check
```

Results:

- Targeted API gate subset: 7 passed.
- `tests/test_answer_intent_classifier.py`: 62 passed.
- `tests/test_answer_eval.py`: 9 passed.
- `tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py`: 232 passed.
- 264-row question-bank classifier validation:
  - `rows`: 264
  - `contract_key_mismatches`: 0
  - `enum_mismatches`: 0
  - `offdomain_or_unsafe_domain_mismatches`: 0
  - `offdomain_or_unsafe_retrieval_mismatches`: 0
  - `offdomain_or_unsafe_sources_mismatches`: 0
  - `offdomain_or_unsafe_fretboard_mismatches`: 0
  - `nonposition_fretboard_overclassified`: 0
  - `source_backed_steel_retrieval_disabled`: 0
- Full pytest: 655 passed.
- `git diff --check`: passed.

## Risks

- The current classifier still returns `off_domain/unknown` for some ambiguous prompts that existing steel routes answer well. This implementation intentionally does not gate that default. A future classifier refinement can reduce ambiguity, but the runtime gate should remain conservative until QA approves broader behavior.
- Existing curated `scope_guardrail` behavior remains in place. The new classifier gate runs earlier for explicit off-domain/unsafe classes, so guardrail copy now comes from `steel_guitar_rag/api.py` for those cases.
- The worktree remains dirty from multiple lanes. Repo Steward must stage exact hunks only.

## What Was Not Touched

- Chroma/vector stores
- embeddings
- scraping
- corpus-private
- corpus-v2
- source-inbox
- provenance/legal files
- deployment/DNS/.wrangler
- UI files
- source-card UI
- answer-page layout
- teacher-first answer composer
- retrieval ranking
- auth/access-control logic

## Exact Next QA Prompt For Lane 15 / Answer Eval

```text
QA the retrieval-gating implementation.

Read:
- AGENTS.md
- docs/llm-guidance/answer-contract.md
- docs/handoffs/task-completions/retrieval-gating-implementation-plan.md
- docs/handoffs/task-completions/qa-retrieval-gating-plan-review.md
- docs/handoffs/task-completions/retrieval-gating-implementation.md
- steel_guitar_rag/api.py
- steel_guitar_rag/answer_intent_classifier.py
- tests/test_api_search.py
- tests/answer_eval/question_bank.jsonl

Verify:
1. "What is the capital of France?" returns a scoped guardrail without retrieval, sources, warnings, or fretboard.
2. "Write me a Python script to scrape Instagram." returns a guardrail without retrieval, sources, warnings, or fretboard.
3. "Show me all of the numbers between 1 and 1 million." returns a guardrail without retrieval, sources, warnings, or fretboard.
4. Valid steel prompts still retrieve when source-backed:
   - What are common uses for the E9 9th string?
   - Who was Buddy Emmons?
   - Is Mullen or MSA a better guitar?
   - What vendors sell pedal steel accessories?
5. Position prompts still return fretboard when already supported:
   - Where can I play a G chord?
   - Where can I play a C chord?
6. No classifier metadata is exposed in public /api/answer JSON.
7. Teacher-first composer/source-card/UI behavior was not changed.

Run:
- .venv/bin/python -m pytest tests/test_answer_intent_classifier.py
- .venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py
- the 264-row question-bank classifier validation
- optional: the exact 12-prompt browser smoke from docs/handoffs/task-completions/browser-smoke-answer-ui.md

Write docs/handoffs/task-completions/qa-retrieval-gating-implementation.md with pass/fail, remaining risks, and commit readiness.
```

## Ready For QA

Yes. This slice is ready for Lane 15 QA.

## Safe-To-Stage Guidance

For this lane, the intended safe-to-stage scope is:

- `steel_guitar_rag/api.py`
- the retrieval-gating test hunks in `tests/test_api_search.py`
- `docs/handoffs/task-completions/retrieval-gating-implementation.md`

Because `tests/test_api_search.py` already contains unrelated dirty hunks from prior lanes, stage with hunk review. Do not use `git add .`.

Must remain unstaged unless separately approved:

- Chroma/vector DBs
- embeddings
- corpus-private generated output
- corpus-v2 generated output
- source-inbox data
- scraping/provenance/legal generated files
- deployment/DNS/.wrangler files
- UI/design assets
