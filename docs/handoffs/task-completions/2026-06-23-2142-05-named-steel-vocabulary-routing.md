# 2026-06-23 21:42 - Lane 05 - Named Steel Vocabulary Routing

## Task Summary

Fixed the backend routing gap where named steel-guitar vocabulary prompts such as `What does a Franklin pedal do?` could fall into the generic specificity fallback instead of receiving a direct teacher-first answer.

Completed:
- Added deterministic named steel vocabulary classification for core copedent/mechanics terms.
- Added curated teacher-first definitions for Franklin pedal/change, zero pedal, half stop, split tuning, compensator, vertical lever, F lever, E lever, X lever, Emmons setup, Day setup, Crawford cluster, and copedent.
- Preserved source-seeking behavior for usage questions such as player/forum usage prompts.
- Added classifier and API regression coverage with noisy fake sources.

Intentionally not changed:
- No UI changes.
- No corpus, Chroma, embedding, scraper, auth, DNS, deployment, launchd, tunnel, secret, or private-source changes.
- No tab generation and no copyrighted content behavior changes.

## Files Changed

- `steel_guitar_rag/answer_intent_classifier.py`
- `steel_guitar_rag/curated_answers.py`
- `tests/test_answer_intent_classifier.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-23-2142-05-named-steel-vocabulary-routing.md`

## Tests And Checks

Passed:
- `git diff --check`
- `.venv/bin/python -m py_compile steel_guitar_rag/api.py steel_guitar_rag/curated_answers.py steel_guitar_rag/answer_intent_classifier.py`
- `.venv/bin/python -m pytest tests/test_answer_intent_classifier.py -q`
- `.venv/bin/python -m pytest tests/test_api_search.py -k 'franklin or pedal or lever or copedent or half_stop or split or compensator or named' -q`
- `.venv/bin/python -m pytest tests/test_api_search.py -q`
- `.venv/bin/python -m pytest tests/test_api_contract.py -q`

Results:
- `tests/test_answer_intent_classifier.py`: 100 passed
- focused `tests/test_api_search.py -k ...`: 11 passed, 268 deselected
- `tests/test_api_search.py`: 279 passed
- `tests/test_api_contract.py`: 5 passed

## Integration Notes

Named definition prompts now classify as:

```json
{
  "domain": "steel_guitar",
  "intent": "copedent_position",
  "needs_sources": false,
  "needs_fretboard": false,
  "needs_copedent": true,
  "retrieval_allowed": false,
  "allowed_answer_shape": "copedent_position"
}
```

The classifier keeps explicit source-seeking usage prompts source-backed. Example: `How do players use the F lever in real songs?` remains retrieval-allowed because it asks what players do, not just what the term means.

API behavior for the named vocabulary prompts:
- Teacher-first direct answer.
- `sources: []`.
- `warnings: []`.
- No `fretboard` by default.
- No `tab_example` by default.
- No generic specificity fallback.

## Risk Assessment

Risk: low.

Reason: this is a narrow pre-retrieval curated-answer addition and classifier rule. It does not change retrieval, source-card rendering, UI, or response schema. The main behavior tradeoff is that basic named-term definition prompts are now source-free deterministic answers. Explicit usage/source-seeking prompts still retrieve.

Rollback:
- Revert the named vocabulary regex/routing addition in `steel_guitar_rag/answer_intent_classifier.py`.
- Remove `NAMED_STEEL_VOCABULARY_*` helpers and pre-retrieval hook calls in `steel_guitar_rag/curated_answers.py`.
- Remove the two focused test additions.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `steel_guitar_rag/answer_intent_classifier.py`
- `steel_guitar_rag/curated_answers.py`
- `tests/test_answer_intent_classifier.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-23-2142-05-named-steel-vocabulary-routing.md`

## Files That Must Not Be Staged

Unrelated parked dirty/untracked files remain in the worktree, including docs, corpus metadata, source-inbox files, scripts, deployment/design assets, and UI brand assets. Do not stage broad paths or use `git add .`.

## Recommended Next Lane

Lane 12 or Lane 15 can smoke the protected preview prompt:

```text
What does a Franklin pedal do?
```

Expected: direct teacher-first answer mentioning the common Franklin change and copedent variation, with no generic specificity fallback.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 12 protected-preview smoke after the backend commit is available in runtime.
