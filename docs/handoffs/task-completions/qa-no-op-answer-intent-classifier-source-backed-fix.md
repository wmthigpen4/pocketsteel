# QA No-Op Answer Intent Classifier Source-Backed Fix

## Task summary
- What was requested: re-review the Lane 05 source-backed classifier fix, verify the focused tests and 264-row question-bank classifier validation pass, confirm `/api/answer` still calls the classifier as a no-op hook, and decide whether QA approves commit.
- What was completed: read the required repo guidance, answer contract, eval rubric, question bank, integration status, prior QA handoff, Lane 05 source-backed fix handoff, classifier implementation, classifier tests, answer-eval tests, and `/api/answer` implementation. Ran the requested test commands plus a fresh explicit 264-row validation counter.
- What was intentionally not changed: no implementation files, UI files, tests, fixtures, corpus data, source data, Chroma/vector stores, embeddings, scraping, deployment, DNS, runtime answer behavior, or staging/commits were modified.

## Files changed
- Changed files: none from this QA review.
- Created files:
  - `docs/handoffs/task-completions/qa-no-op-answer-intent-classifier-source-backed-fix.md`
- Deleted files: none.
- Generated artifacts: none.

## Pass/fail decision
- Decision: **Pass / QA approves commit for the narrow no-op classifier slice**.
- Summary: the prior guardrail/fretboard drift and source-backed retrieval drift are all cleared in the explicit question-bank validation. Focused classifier, answer-eval, API/search, and full answer-quality tests passed. `/api/answer` still only calls the classifier as a no-op hook and does not expose classifier metadata or enable retrieval gating.

## Exact question-bank mismatch counts
Question-bank validation checked `264` rows from `tests/answer_eval/question_bank.jsonl`.

- `contract_key_mismatches`: 0
- `invalid_domain_enum`: 0
- `invalid_intent_enum`: 0
- `invalid_shape_enum`: 0
- `offdomain_or_unsafe_domain_mismatches`: 0
- `offdomain_or_unsafe_retrieval_mismatches`: 0
- `impossible_or_large_output_misclassified_as_steel`: 0
- `impossible_or_large_output_retrieval_allowed`: 0
- `non_fretboard_expected_but_classifier_needs_fretboard`: 0
- `steel_source_backed_expected_retrieval_but_classifier_disallows`: 0
- `steel_source_backed_expected_but_off_domain`: 0

Additional probe results:
- Position probe failures: none.
- Source-backed probe failures: none.

## Verification results
- Focused classifier tests: pass.
- Broader question-bank classifier validation: pass.
- Off-domain/unsafe retrieval guard: pass.
- Impossible/large-output guard: pass.
- Non-position `needs_fretboard` over-routing: pass.
- Source-backed steel retrieval: pass.
- Player/history/bio prompts: classify as `steel_guitar` with `retrieval_allowed=true`.
- Brand/manufacturer/source prompts: classify as `steel_guitar` with `retrieval_allowed=true`.
- Vendor/accessory prompts: classify as `steel_guitar` with `retrieval_allowed=true`.
- Practical gear prompts: classify as `steel_guitar` with `retrieval_allowed=true`.
- Obvious position/fretboard prompts: still classify with `needs_fretboard=true`.
- `/api/answer` hook: pass. `steel_guitar_rag/api.py` imports `classify_answer_request` and calls it after `parse_answer_request(...)`:
  - `_answer_intent_decision = classify_answer_request(answer_request.question, answer_request.mode)`
- `/api/answer` public response shape: pass. Existing classifier test verifies the public response contains only `answer`, `mode`, `sources`, `warnings`, and `sections`, with no `intent`, `intent_mode`, `answer_intent`, or `retrieval_allowed`.
- Retrieval gating: not enabled. The classifier decision remains assigned to `_answer_intent_decision` and is not used for branching.
- UI files: no UI files were touched by this QA task or by the narrow classifier slice. The broader worktree still contains unrelated parked UI/design files.

## Tests and checks
- `git status --short`
  - Result: broad dirty worktree remains. Relevant classifier files are uncommitted, and many unrelated UI/design/provenance/corpus-adjacent files remain parked.
- `git diff --check`
  - Result: passed.
- `.venv/bin/python -m pytest tests/test_answer_intent_classifier.py`
  - Result: passed, `62 passed`.
- `.venv/bin/python -m pytest tests/test_answer_eval.py`
  - Result: passed, `9 passed`.
- `.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py`
  - Result: passed, `228 passed`.
- Narrow 264-row question-bank classifier validation:
  - Result: passed; all tracked mismatch counts are 0.
- Tests skipped:
  - Full pytest was not run because the user requested focused classifier/API/eval checks plus the explicit 264-row validation; all requested checks passed.

## QA approval
- QA approves commit for the narrow no-op classifier scaffold/fix slice.
- This approval does not approve retrieval gating, runtime behavior changes, UI changes, Chroma/embedding/corpus changes, deployment changes, DNS changes, or unrelated dirty worktree files.

## Files that should be included in the commit if approved
Recommended narrow safe-to-stage list:
- `steel_guitar_rag/answer_intent_classifier.py`
- `steel_guitar_rag/api.py`
- `tests/test_answer_intent_classifier.py`
- `docs/handoffs/task-completions/no-op-answer-intent-classifier-fix.md`
- `docs/handoffs/task-completions/no-op-answer-intent-classifier-drift-fix.md`
- `docs/handoffs/task-completions/no-op-answer-intent-classifier-source-backed-fix.md`
- `docs/handoffs/task-completions/qa-no-op-answer-intent-classifier-source-backed-fix.md`

Optional Repo Steward judgment:
- Prior blocking QA handoffs can remain parked as coordination history unless Repo Steward wants to include the audit trail in the same commit:
  - `docs/handoffs/task-completions/qa-no-op-answer-intent-classifier-fix.md`
  - `docs/handoffs/task-completions/qa-no-op-answer-intent-classifier-drift-fix.md`

## Files that should remain parked
- All UI/design/landing files, including `ui/`, `ui/brand/`, `public/`, `Neon Sign/`, `deploy/landing/index.html`, and frontend demo files.
- All corpus/source/provenance/private/generated data and reports.
- Chroma/vector stores, embeddings, scraping outputs, `.wrangler/`, deployment/DNS/secrets.
- Broad unrelated dirty files from other lanes.
- Older no-op handoffs not listed in the safe-to-stage list unless Repo Steward explicitly decides to include them.

## Integration notes
- The classifier is deterministic regex logic with stdlib imports only; no LLM, network, Chroma, retrieval, or answer generation call was added to the classifier.
- The public `/api/answer` response contract is unchanged.
- The classifier now matches the broad answer-eval question bank on the tracked pre-gating dimensions.
- Retrieval gating remains a separate YELLOW task and must not be bundled into this commit.
- Human decision needed: no for QA. Repo Steward may proceed with a narrow exact-path commit if desired.

## Risk assessment
- Risk: Low to Medium.
- Why: user-facing runtime behavior remains unchanged, so direct product risk is low. Coordination risk is medium because the repo worktree is broadly dirty and staging must be exact-path only.
- Rollback notes: revert the classifier file, classifier test file, `/api/answer` no-op import/call, and associated handoffs if the scaffold needs to be backed out.

## Commit readiness
Safe to commit

## Suggested next step
- Next lane: 01 Repo Steward.
- Exact recommended prompt for 01:

```text
Lane 01 Repo Steward: commit the QA-approved no-op answer intent classifier scaffold only.

Read:
- docs/handoffs/task-completions/qa-no-op-answer-intent-classifier-source-backed-fix.md

Stage narrowly:
- steel_guitar_rag/answer_intent_classifier.py
- steel_guitar_rag/api.py
- tests/test_answer_intent_classifier.py
- docs/handoffs/task-completions/no-op-answer-intent-classifier-fix.md
- docs/handoffs/task-completions/no-op-answer-intent-classifier-drift-fix.md
- docs/handoffs/task-completions/no-op-answer-intent-classifier-source-backed-fix.md
- docs/handoffs/task-completions/qa-no-op-answer-intent-classifier-source-backed-fix.md

Do not stage UI files, corpus/source/provenance files, generated reports, private data, Chroma, embeddings, scraping changes, deployment files, design assets, or unrelated docs/tests/scripts.

Before committing, run:
git diff --cached --check
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py

Commit with a message like:
Add no-op answer intent classifier
```

- Exact next prompt for 05 Backend / RAG Integration if commit is not approved:

```text
Lane 05 Backend / RAG Integration: no further classifier fix is requested by QA at this time. If Repo Steward declines the commit, inspect the staged diff concerns and keep runtime behavior unchanged unless a new task explicitly approves retrieval gating.
```
