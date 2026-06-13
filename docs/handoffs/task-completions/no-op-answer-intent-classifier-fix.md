# No-Op Answer Intent Classifier Fix

Date: 2026-06-13 02:14:20 -0500
Branch: feature/answer-api
HEAD: 4124b88

## What QA Blocked

QA blocked the parked no-op classifier because the implementation did not yet match the planned integration seam:

- The classifier exposed `classify_answer_intent(question)` but QA expected an `/api/answer` request-level function, `classify_answer_request(question, mode="ask")`.
- `/api/answer` did not call the classifier at the answer entry point.
- There was no test proving the classifier remains internal and does not alter the public `/api/answer` response shape.

The broad question-bank comparison also showed many expected/actual differences. This fix addresses the immediate no-op contract blockers without enabling retrieval gating or changing answer behavior.

## Files Changed

- `pocketsteel/answer_intent_classifier.py`
- `pocketsteel/api.py`
- `tests/test_answer_intent_classifier.py`
- `docs/handoffs/task-completions/no-op-answer-intent-classifier-fix.md`

## Exact Classifier Contract Behavior

`classify_answer_request(question: str, mode: str = "ask")` now returns exactly:

```json
{
  "domain": "steel_guitar|off_domain|unsafe_or_impossible",
  "intent": "forum_wisdom|copedent_position|gear_diagnosis|practice_plan|tab_explainer|lesson_lookup|small_talk|unknown",
  "needs_sources": true,
  "needs_fretboard": false,
  "needs_copedent": false,
  "retrieval_allowed": true,
  "allowed_answer_shape": "source_backed|copedent_position|gear_diagnosis|practice_plan|tab_explainer|guardrail_refusal"
}
```

`classify_answer_intent(question)` remains as a compatibility wrapper around `classify_answer_request(question)`.

Classification remains deterministic and conservative:

- Obvious steel-guitar questions route to `steel_guitar`.
- Source-seeking steel questions route to `forum_wisdom`.
- Obvious position/fretboard questions route to `copedent_position` with `needs_fretboard=true`.
- Non-position steel questions keep `needs_fretboard=false`.
- Gear/hum/buzz/tuner questions route to `gear_diagnosis`.
- Practice-plan questions route to `practice_plan`.
- Tab/interval questions route to `tab_explainer`.
- Off-domain questions route to `off_domain`, `retrieval_allowed=false`.
- Unsafe/impossible mass-output or scraping requests route to `unsafe_or_impossible`, `retrieval_allowed=false`.

## `/api/answer` Hook

Hook location:

- `pocketsteel/api.py`
- `RetrievalApi.__call__`
- After `parse_answer_request(...)` succeeds
- Before deterministic curated/fretboard routes and before retrieval

The hook calls:

```python
_answer_intent_decision = classify_answer_request(answer_request.question, answer_request.mode)
```

The result is intentionally unused in this slice. No retrieval gating, source filtering, answer text changes, fretboard changes, or response-shape changes are enabled.

## Proof Public `/api/answer` Behavior Did Not Change

Added `tests/test_answer_intent_classifier.py::test_api_answer_calls_classifier_without_exposing_public_metadata`.

This test:

- Monkeypatches `pocketsteel.api.classify_answer_request`.
- Calls the real WSGI `/api/answer` path.
- Verifies the classifier was called with `(question, mode)`.
- Verifies the public response keys remain exactly:
  - `answer`
  - `mode`
  - `sources`
  - `warnings`
  - `sections`
- Verifies classifier metadata such as `intent`, `intent_mode`, `answer_intent`, and `retrieval_allowed` is not exposed.

## Tests Added Or Updated

Updated classifier coverage for the requested examples:

- `What are common uses for the E9 9th string?`
- `Why would a player prefer a wound 6th string?`
- `What do players say about using the 6th string lower?`
- `Explain B+C pedals.`
- `Where are my G chord positions?`
- `Show me C positions on E9.`
- `How do players diagnose hum that changes when touching the changer?`
- `What are common Fender Steel King settings?`
- `Build a 7-day practice plan for blocking.`
- `Explain this tab in intervals.`
- `What is the capital of France?`
- `Write me a Python script to scrape Instagram.`

Added request-level and API-hook tests:

- `test_classify_answer_request_accepts_mode_without_changing_contract_shape`
- `test_api_answer_calls_classifier_without_exposing_public_metadata`

## Tests Run And Results

Passed:

```bash
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py
```

Result: `24 passed`

Passed:

```bash
git status --short
git diff --check
.venv/bin/python -m pytest tests/test_api_search.py tests/test_api_contract.py
```

Result: `187 passed`

Passed:

```bash
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py tests/test_answer_eval.py tests/test_full_answer_quality_eval.py
```

Result: `74 passed`

`git diff --check` passed with no whitespace errors.

Full pytest was not run because the requested scope was the no-op classifier repair and current repo guidance did not require an expensive full suite for this slice.

## Remaining Risks

- The classifier is still no-op and intentionally does not block retrieval or alter answers.
- The broad question-bank classifier expectation file may still need QA normalization where product terms differ from classifier terms, such as `fretboard_allowed` versus `needs_fretboard`.
- The repo worktree contains many unrelated dirty and untracked files from earlier lanes. Repo Steward should stage only the safe list below.

## Exact Next Prompt For 15 QA / Answer Eval

QA the no-op answer intent classifier repair. Verify:

1. `classify_answer_request(question, mode="ask")` exists and returns the exact contract keys/enums.
2. `classify_answer_intent(question)` remains backward-compatible.
3. `/api/answer` calls the classifier after request parsing.
4. `/api/answer` public response shape does not expose classifier metadata.
5. Off-domain and unsafe examples classify with `retrieval_allowed=false`.
6. Steel-guitar position examples set `needs_fretboard=true` only when appropriate.
7. No retrieval gating or public answer behavior changed.

Run:

```bash
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py tests/test_api_search.py tests/test_api_contract.py tests/test_answer_eval.py tests/test_full_answer_quality_eval.py
git diff --check
```

## Exact Next Prompt For 01 Repo Steward

Review the no-op answer intent classifier repair for commit readiness. Stage only the safe-to-stage files listed below. Confirm no unrelated dirty files, generated data, corpus-private files, Chroma/vector stores, embeddings, source-inbox data, deployment files, DNS config, or design assets are staged.

Suggested commit message:

```text
Add no-op answer intent classifier hook
```

## Commit Readiness

Ready for Repo Steward review: yes.

Human decision needed before enabling retrieval gating: yes.

## Safe-To-Stage File List

- `pocketsteel/answer_intent_classifier.py`
- `pocketsteel/api.py`
- `tests/test_answer_intent_classifier.py`
- `docs/handoffs/task-completions/no-op-answer-intent-classifier-fix.md`

## Must Remain Unstaged

- `corpus-private/`
- `corpus-v2/`
- `source-inbox/`
- `data/`
- Chroma/vector stores
- embeddings
- raw corpus data
- generated reports unless explicitly approved
- deployment secrets
- `.wrangler`
- DNS config
- UI brand/design assets
- all unrelated dirty/untracked files shown by `git status --short`
