# Chord Plan Typo Routing

## Task Summary
- What was requested: stop chord-position typo questions such as `How do I plan an F chord?` from falling through to SGF retrieval fragments.
- What was completed: added a high-confidence deterministic parser route for `plan a/an <root> chord` when root/chord language is present, updated answer-quality eval detection for the typo shape, and added regressions proving F major routes to pitch math with a fretboard payload and empty sources.
- What was intentionally not changed: no deployment, DNS, Chroma/vector store, embeddings, scraping, corpus data, auth, private source exposure, or frontend/UI behavior.

## Files Changed
- Changed files:
  - `pocketsteel/fretboard_examples.py`
  - `scripts/run_full_answer_quality_eval.py`
  - `tests/fixtures/user_question_bank.json`
  - `tests/test_answer_eval.py`
  - `tests/test_api_search.py`
  - `tests/test_fretboard_examples.py`
  - `tests/test_full_answer_quality_eval.py`
- Created files:
  - `docs/handoffs/task-completions/2026-06-12-2110-05-chord-plan-typo-routing.md`
- Deleted files: none.
- Generated artifacts:
  - `/tmp/f-plan-answer.json` from local curl verification; not part of repo.

## Tests And Checks
- `.venv/bin/python -m pytest tests/test_fretboard_examples.py tests/test_api_search.py tests/test_answer_eval.py tests/test_full_answer_quality_eval.py`
  - Result: 211 passed.
- `.venv/bin/python -m pytest`
  - Result: 493 passed.
- `git diff --check`
  - Result: passed.
- Local curl verification:
  - Command:
    ```bash
    curl -sS -X POST "http://127.0.0.1:8783/api/answer" \
      -H "Content-Type: application/json" \
      -H "X-Steel-Rag-Dev-Access-Role: beta_user" \
      -d '{"question":"How do I plan an F chord?","mode":"ask","topK":6}' \
      | python3 -m json.tool
    ```
  - Result:
    - Answer included F major at 1st fret open, 4th fret A+F, and 8th fret A+B.
    - `sources: []`
    - `warnings: []`
    - `fretboard.title: F major positions on E9`
    - Visible starter positions: `f-open-1`, `f-af-4`, `f-ab-8`

## Integration Notes
- Root cause found:
  - The deterministic chord-position router matched `How do I play...` and `How do I make...`, but not the likely typo `How do I plan an F chord?`.
  - Because the router missed the query, `/api/answer` could continue to SGF retrieval and synthesize unrelated chord fragments.
- Behavior after fix:
  - `How do I plan an F chord?` is treated as a likely typo for `play` only when the query includes a valid root and explicit `chord` wording.
  - Non-chord uses of `plan`, such as `How do I plan my practice tonight?`, do not get forced into the fretboard route.
  - Deterministic chord-position answers still return top-level `sources: []` and no weak-source warning.
- Before/after answer:
  - Before: SGF-fragment answer mentioned unrelated A-root/F-chord fragments, `F#7 > B7 > E7 > A7`, and Mel Bay chart chatter.
  - After: `On standard E9, several useful F major starter positions are: 1st fret no pedals; 4th fret with A pedal + F lever; 8th fret with A+B pedals.`
- Assumptions:
  - `plan a/an <root> chord` is high-confidence typo only when root/chord syntax is present.
  - Low-confidence planning questions should continue through the normal answer/fallback path rather than trigger fretboard visualization.
- Blockers: none.
- Human decisions needed: no.

## Risk Assessment
- Risk: Low.
- Why: the route is narrow, deterministic, and covered by parser/API/eval tests. It does not alter retrieval, storage, auth, or frontend behavior.
- Rollback notes: remove the `how do i plan ... chord` regex branch and the associated tests/fixture row to return to previous behavior.

## Commit Readiness
- Safe to commit.

## Suggested Next Step
- Lane 06 UX/UI or QA can include `How do I plan an F chord?` in the protected-preview smoke pass to verify the UI shows the F major selector and no SGF source cards.
