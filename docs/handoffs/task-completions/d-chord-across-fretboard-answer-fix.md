# D Chord Across Fretboard Answer Fix

## Task Summary

Requested: fix the protected-preview failure for `How do I play a D chord across the fretboard of the E9?`, where the answer fell through to source-fragment synthesis, omitted `response.fretboard`, and failed to present deterministic E9 positions.

Completed: widened the deterministic major-chord position parser so D-across-fretboard phrasing routes through the existing pitch-math fretboard engine before retrieval. Added scoped answer text enrichment for across-the-fretboard major-chord prompts so D answers include starter positions plus useful lower-octave and E-lower alternates when validated by the engine.

Intentionally not changed: no UI files, no source-card UI, no deployment/DNS/auth, no Chroma, no embeddings, no scraping, no corpus/private/source-inbox/generated data. No staging or commit was performed.

Branch/HEAD at verification: `feature/answer-api` / `25c0ffe`.

## Root Cause

The D question was chord-position shaped, but `major_chord_location_request_for_question()` did not recognize variants such as:

- `How do I play a D chord across the fretboard of the E9?`
- `Show me D chord positions on E9.`
- `Where are D chord positions on E9?`
- `D major across the E9 fretboard`

Because the deterministic router missed those phrasings, `/api/answer` continued into retrieval/source-fragment answer assembly. The pitch engine already knew the D positions; the missing piece was pre-retrieval classification.

## Files Changed

- `pocketsteel/fretboard_examples.py`
  - Added major chord-position parser patterns for `across the fretboard`, `show me <root> chord positions`, and `where are <root> chord positions` phrasing.
- `pocketsteel/curated_answers.py`
  - Added across-fretboard answer enrichment for deterministic major chord answers, using already validated lower-octave A+B and E-lower positions when present.
- `tests/test_fretboard_examples.py`
  - Added D major parser/payload regression coverage.
- `tests/test_api_search.py`
  - Added API-level regression coverage for the protected-preview D prompt.
- `docs/handoffs/task-completions/d-chord-across-fretboard-answer-fix.md`
  - This handoff.

Note: these implementation/test files were already dirty from previous backend lanes. Repo Steward should review and stage exact hunks for this D-fix slice only.

## Behavior Before / After

Before:

- The D prompt returned source-fragment-like text such as references to Am7 scales over D and open D-string fragments.
- No top-level `response.fretboard` was attached.
- Retrieval source cards could appear for a deterministic chord-position question.

After:

- The D prompt returns a deterministic teacher-first answer:
  - `10th fret, no pedals: open-position D major`
  - `13th fret with A pedal + F lever: A+F D major position`
  - `17th fret with A+B pedals: A+B D major position`
  - across-fretboard alternates:
    - `5th fret with A+B pedals`
    - `3rd fret with E-lower`
- Top-level `response.fretboard` is attached.
- The fretboard payload includes validated D positions such as:
  - `d-open-10`
  - `d-af-13`
  - `d-ab-17`
  - `d-ab-5-lower-octave`
  - `d-e-lower-5-7-8-3`
- Top-level sources are suppressed for this deterministic chord-position route: `sources: []`.
- Warnings remain clean: `warnings: []`.

## Tests And Checks

Commands run:

```bash
.venv/bin/python -m pytest tests/test_fretboard_examples.py::test_d_major_across_fretboard_position_prompts_are_supported tests/test_api_search.py::test_remaining_retrieval_gating_smoke_failures_get_teacher_first_answers
```

Result: `2 passed`.

```bash
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py
```

Result: `62 passed`.

```bash
.venv/bin/python -m pytest tests/test_answer_eval.py
```

Result: `9 passed`.

```bash
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py
```

Result: `234 passed`.

Question-bank classifier validation:

- Rows checked: `264`
- Failures: `0`

```bash
.venv/bin/python -m pytest
```

Result: `662 passed`.

```bash
git diff --check
```

Result before final handoff write: passed. Re-run after this handoff before closeout.

## Integration Notes

- This is a parser/routing fix, not a new broad answer composer.
- The fix is general for major chord-position phrasing, not a single hardcoded exact prompt.
- The answer text enrichment is intentionally limited to prompts that mention both `across` and `fretboard`.
- Existing G/C/A/B/C#/B# deterministic chord-position behavior should remain intact.
- UI should now receive the same top-level `response.fretboard` contract used by other deterministic chord-position answers.

## Risk Assessment

Risk: low to medium.

Why: the code path is narrow and covered by focused + full test runs, but the working tree is heavily dirty and the touched files contain overlapping changes from prior lanes. Commit/staging risk is mostly git hygiene, not runtime behavior.

Rollback: revert the added parser patterns in `pocketsteel/fretboard_examples.py`, the across-fretboard enrichment block in `pocketsteel/curated_answers.py`, and the D-specific test additions.

## Commit Readiness

Safe to commit after Repo Steward hunk-level review.

Safe-to-stage file list for this slice:

- `pocketsteel/fretboard_examples.py`
- `pocketsteel/curated_answers.py`
- `tests/test_fretboard_examples.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/d-chord-across-fretboard-answer-fix.md`

Must remain unstaged unless separately approved:

- UI files
- deploy/DNS/Cloudflare files
- Chroma/vector stores
- embeddings
- `corpus-private/`
- `corpus-v2/`
- `source-inbox/`
- generated reports/data
- provenance/legal/source-ingestion artifacts
- design assets and `Neon Sign/`
- unrelated dirty files from other lanes

## Suggested Next Step

Lane 15 QA / Answer Eval should rerun the authenticated D-chord protected-preview smoke:

```text
On the protected-preview UI, ask: “How do I play a D chord across the fretboard of the E9?”

Verify:
- answer is deterministic and teacher-first
- D positions include 10 open, 5 A+B lower-octave, 3 E-lower if shown, and 17 A+B
- top-level fretboard renders
- no raw SGF/source fragments appear in the main answer
- no weak-source warning
- source cards are absent or clearly not unrelated retrieval evidence
```
