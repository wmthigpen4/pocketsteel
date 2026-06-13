# No-Op Answer Intent Classifier Drift Fix

Date: 2026-06-13
Branch: feature/answer-api
HEAD: 4124b88

## QA Blocker Addressed

QA found that the no-op answer intent classifier drifted from the documented contract:

- off-domain and unsafe/impossible prompts still allowed retrieval;
- several large-output/private-data/copyright prompts were not classified as `unsafe_or_impossible`;
- non-position steel prompts over-classified as `needs_fretboard=true`.

This fix tightens classifier internals and tests only. `/api/answer` still calls the classifier as a no-op hook, does not use the decision for routing, and does not expose classifier metadata in public response JSON.

## Files Changed

- `pocketsteel/answer_intent_classifier.py`
- `tests/test_answer_intent_classifier.py`
- `docs/handoffs/task-completions/no-op-answer-intent-classifier-drift-fix.md`

Related existing hook diff:

- `pocketsteel/api.py` imports and calls `classify_answer_request(...)`; the returned decision remains unused.

## Classifier Rule Changes

- Added guardrail-first classification before steel/off-domain routing.
- Classified mass-output and impossible-output prompts as `unsafe_or_impossible`, including:
  - large repeat requests such as `10,000 times`;
  - huge page/diagram generation;
  - `all/every post`, `every email`, `all passwords`;
  - private corpus/transcript and embedding-vector extraction;
  - full copyrighted or note-for-note album/tab requests.
- Treated `no steel guitar references` / `without steel guitar references` as off-domain context, even if the words `steel guitar` appear.
- Reduced fretboard over-routing:
  - `needs_fretboard=true` now requires explicit visual/location language such as positions, frets, grips, pockets, chord locations, or “show ... positions.”
  - buying prompts, technique-feel prompts, broad practice plans, and missing-context prompts like `this position` / `this chord` stay `needs_fretboard=false`.
- Kept non-visual copedent/mechanics questions as `copedent_position` with `needs_copedent=true`, `needs_fretboard=false`.

## Contract Behavior

Off-domain guardrails now return:

```json
{
  "domain": "off_domain",
  "retrieval_allowed": false,
  "needs_sources": false,
  "needs_fretboard": false,
  "allowed_answer_shape": "guardrail_refusal"
}
```

Unsafe/impossible guardrails now return:

```json
{
  "domain": "unsafe_or_impossible",
  "retrieval_allowed": false,
  "needs_sources": false,
  "needs_fretboard": false,
  "allowed_answer_shape": "guardrail_refusal"
}
```

## Question-Bank Validation

Added a question-bank sanity test over `tests/answer_eval/question_bank.jsonl` that verifies:

- every classifier result has the exact contract keys and valid enum values;
- rows with `expected_domain` of `off_domain` or `unsafe_or_impossible` classify to that domain and disable retrieval/source/fretboard needs;
- rows with `fretboard_allowed=false` return `needs_fretboard=false`.

Result: passing as part of `tests/test_answer_intent_classifier.py`.

## Tests Run

```bash
git status --short
git diff --check
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py
.venv/bin/python -m pytest tests/test_answer_eval.py
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py
git diff --check
```

Results:

- `tests/test_answer_intent_classifier.py`: 40 passed
- `tests/test_answer_eval.py`: 9 passed
- `tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py`: 228 passed
- `git diff --check`: passed

Full pytest was not run for this narrow no-op slice.

## Behavior Confirmations

- Retrieval gating is still disabled.
- The classifier decision is still unused by `/api/answer` runtime routing.
- Public `/api/answer` response shape is unchanged.
- No answer text, source rendering, fretboard rendering, or UI files were changed for this task.
- No Chroma, embeddings, corpus, scraping, auth, deployment, or DNS changes were made.

## Remaining Risks

- The classifier is deterministic regex logic, so future QA may expose more phrasing drift.
- Since retrieval gating remains disabled, off-domain/unsafe classifier decisions do not yet affect production answer behavior.
- The repo worktree contains many unrelated dirty/untracked files from other lanes; staging must be selective.

## Safe-To-Stage List

For this classifier drift-fix slice:

- `pocketsteel/answer_intent_classifier.py`
- `tests/test_answer_intent_classifier.py`
- `docs/handoffs/task-completions/no-op-answer-intent-classifier-drift-fix.md`

Include `pocketsteel/api.py` only if Repo Steward is staging the existing approved no-op classifier hook in the same slice.

## Must Remain Unstaged

- Chroma/vector stores, embeddings, corpus-private, corpus-v2, source-inbox data, generated reports not explicitly approved
- deployment secrets, `.wrangler`, DNS config
- UI/brand/design assets
- unrelated dirty files from other lanes

## Exact Next Prompt For Lane 15 QA

Re-run QA for the no-op answer intent classifier drift fix. Verify `tests/test_answer_intent_classifier.py` and the question-bank sanity checks pass, with focus on off-domain/unsafe prompts disabling retrieval in the classifier contract and non-position steel prompts no longer setting `needs_fretboard=true`. Confirm `/api/answer` public response shape remains unchanged and classifier output is not exposed.

## Ready For QA Re-Review

Yes. This slice is ready for Lane 15 QA re-review.
