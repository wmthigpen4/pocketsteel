# 15 QA / Answer Eval: Chord-Position Router Escape Coverage

## Task
Add regression coverage for chord-position routing escapes so loosely phrased chord-position and chord-function questions cannot pass eval when they fall through to SGF fragments, source cards, weak-source warnings, or missing visual payloads.

## Mode
GREEN - QA/eval coverage only.

## Files Changed
- `scripts/run_full_answer_quality_eval.py`
- `tests/fixtures/user_question_bank.json`
- `tests/test_answer_eval.py`
- `tests/test_full_answer_quality_eval.py`

## Bucket Added
- `chord_position_router_escape`

## Question-Bank Cases Added
- `Where are some places to play C chords?`
- `Where can I play C chord?`
- `Show me C positions.`
- `What frets give me C?`
- `I am in the key of G. Where can I play a 6m chord?`
- `Show me the vi chord in G.`
- `Where is Em on E9?`

All were categorized as `e9_fretboard_copedent` with `expected_contract: copedent_fretboard`.

## Coverage Added
- C major router-escape variants must resolve to deterministic C major positions instead of retrieval fragments.
- G `6m` / `vi` and `Em` variants must resolve to E minor.
- Router-escape answers fail if they expose weak-source fallback language, SGF/source fragments, source cards, missing fretboard payloads, missing expected C frets, or missing E minor resolution.
- Deterministic pitch-rule answers are allowed to be no-source answers in the full quality evaluator, matching the product contract for deterministic routes.
- Added a guard so minor/function prompts are not misclassified as plain major chord-position requests.

## Old Failures Now Caught
- Loose C prompt falling through to a retrieval/source-card answer.
- G `6m` prompt falling through to RKL/B7/forum-fragment style material.
- Visualizable deterministic chord/function answers missing `response.fretboard`.
- Deterministic chord/function answers returning non-empty source cards or weak-source warnings.

## Tests Run
- `.venv/bin/python -m pytest tests/test_answer_eval.py tests/test_full_answer_quality_eval.py tests/test_fretboard_examples.py`
  - Result: `78 passed`
- `.venv/bin/python -m pytest`
  - Result: `508 passed`
- `git diff --check`
  - Result: passed

## Risks
- Low. This changes evaluator and fixture coverage only; it does not change runtime answer generation, retrieval, Chroma, embeddings, scraping, deployment, DNS, auth, or app config.
- The new bucket is intentionally strict for the listed router-escape phrasings, so future product changes must keep deterministic no-source visual payload behavior for these prompts.

## Human Decision Needed
No.

## Recommended Next Step
Safe to commit after human review of the diff. Then use this bucket as a gate for any backend routing fix that handles these prompt variants in the live app.
