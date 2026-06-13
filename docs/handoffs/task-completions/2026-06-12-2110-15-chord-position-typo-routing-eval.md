# 2026-06-12 21:10 - Lane 15 - Chord-Position Typo Routing Eval

## Task summary
- Requested: add eval coverage for chord-position typo routing, especially `How do I plan an F chord?`.
- Completed:
  - Added failure bucket `chord_position_typo_fallback_failure`.
  - Added question-bank coverage for F chord typo/control variants:
    - `How do I plan an F chord?`
    - `How do I play an F chord?`
    - `How do I make an F chord?`
    - `Where can I play an F chord?`
  - Added evaluator tests proving typo fallback failures are caught when answers use SGF/source fragments, omit fretboard payloads, omit deterministic F frets, return sources, or expose weak-source warnings.
  - Added evaluator pass coverage for a clean F answer with fret 1 open/no pedals, fret 4 A+F, and fret 8 A+B.
- Intentionally not changed:
  - Runtime answer behavior, Chroma/vector stores, embeddings, scraping, deployment, DNS, generated/private reports, staging, and commits.

## Files changed
- Changed files:
  - `scripts/run_full_answer_quality_eval.py`
  - `tests/fixtures/user_question_bank.json`
  - `tests/test_answer_eval.py`
  - `tests/test_full_answer_quality_eval.py`
- Created files:
  - `docs/handoffs/task-completions/2026-06-12-2110-15-chord-position-typo-routing-eval.md`
- Deleted files:
  - None.
- Generated artifacts:
  - None.

## Tests and checks
- Exact commands run:
  - `.venv/bin/python -m pytest tests/test_answer_eval.py tests/test_full_answer_quality_eval.py`
  - `.venv/bin/python -m pytest`
  - `git diff --check`
- Results:
  - Targeted pytest: `34 passed in 0.15s`.
  - Full pytest: `495 passed in 3.98s`.
  - `git diff --check`: passed.
- Tests skipped and why:
  - None.

## Integration notes
- The new bucket is intentionally specific to typo-shaped chord-position questions such as `How do I plan an F chord?`.
- The evaluator already recognized `plan` as a likely typo for `play` in chord-position prompts on this branch; this task added dedicated bucket attribution and test coverage.
- The expected F deterministic positions locked by eval are:
  - fret 1 open/no pedals
  - fret 4 with A+F
  - fret 8 with A+B
- Blockers:
  - None.
- Human decisions needed:
  - No.

## Risk assessment
- Low.
- Why:
  - This is eval/test coverage only. It does not alter app routing, retrieval, data stores, auth, scraping, or deployment behavior.
- Rollback notes:
  - Revert the listed eval/test/fixture files and this handoff to remove the typo-routing gate.

## Commit readiness
Safe to commit

## Suggested next step
- Lane 15 can run the full answer-quality eval later to confirm live/local answers for the new F typo/control rows stay green.
