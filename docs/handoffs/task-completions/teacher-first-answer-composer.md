# Teacher-First Answer Composer Backend Slice

Date: 2026-06-13
Branch: `feature/answer-api`
HEAD: `9a7759c`

## Summary

Implemented the smallest backend slice for the screenshot-derived teacher-first failures. The answer path now handles:

- `How do I play a G-minor chord?`
- `How do I play a 1-4-5-1 turnaround?`
- `What’s it mean for a song to be a swing or a waltz?`

The fix keeps sources as supporting evidence when retrieval-backed answers are used, and keeps deterministic fretboard/chord answers source-free when the answer is generated from the pitch/rules layer.

## Files Changed

- `pocketsteel/fretboard_examples.py`
- `pocketsteel/curated_answers.py`
- `tests/test_fretboard_examples.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/teacher-first-answer-composer.md`

No UI files were changed.

## Behavior Added

### G-minor chord

Root cause before fix: `G-minor` with a hyphen was not recognized by the minor-position router, so the request fell through to generic fallback behavior.

After fix:

- `How do I play a G-minor chord?` routes to deterministic minor-position logic.
- The answer explains `G minor = G-Bb-D`, root, minor 3rd, perfect 5th.
- The answer includes validated E9 minor-position examples.
- A top-level `fretboard` payload is included.
- `sources: []`, because this is deterministic pitch-math/rules-layer behavior.

### 1-4-5-1 turnaround

Root cause before fix: the progression prompt had no teacher-first route, so fallback/contract cleanup could produce a generic low-information answer.

After fix:

- The answer explains `1-4-5-1` as `I-IV-V-I`.
- It gives a concrete G example: `G-C-D-G`.
- It gives a practical E9 path: G at 3rd fret open, C at 3rd fret A+B, D at 5th fret A+B, back to G.
- Retrieved source cards remain available as evidence below the synthesized answer.
- No fretboard payload is attached because the prompt is not explicitly asking for a visual/position selector.

### Swing vs. waltz

Root cause before fix: the feel/meter prompt had no teacher-first route, so fallback/contract cleanup could produce a generic low-information answer.

After fix:

- The answer explains swing as a 4/4 long-short/triplet-based feel.
- The answer explains waltz as a 3/4 `1-2-3` feel.
- It connects both to pedal steel: fills, bar movement, blocking, volume-pedal swells, and supporting the vocal.
- Retrieved source cards remain available as evidence below the synthesized answer.
- No fretboard payload is attached.

## Before/After Summaries

### `How do I play a G-minor chord?`

Before: generic fallback: `I don’t have enough reliable information...`

After: `A G minor chord means the notes G-Bb-D: root, minor 3rd, and perfect 5th.` Then validated E9 positions with a fretboard payload.

### `How do I play a 1-4-5-1 turnaround?`

Before: generic fallback: `I don’t have enough reliable information...`

After: explains `I-IV-V-I`, gives `G-C-D-G`, and maps it to simple E9 grips/frets/pedals.

### `What’s it mean for a song to be a swing or a waltz?`

Before: generic fallback: `I don’t have enough reliable information...`

After: explains swing vs. waltz plainly and applies the feel to steel-guitar phrasing.

## Source Evidence

Source evidence remains available for the two non-deterministic teaching answers:

- `1-4-5-1 turnaround` retains source cards from the normal retrieval path.
- `swing or waltz` retains source cards from the normal retrieval path.

The G-minor chord answer is deterministic pitch/rules-layer output and therefore suppresses source cards, matching the existing chord/fretboard behavior.

## Tests Run

- `git status --short`
- `git diff --check`
- `.venv/bin/python -m pytest tests/test_fretboard_examples.py::test_hyphenated_minor_chord_questions_route_to_minor_positions tests/test_api_search.py::test_teacher_first_screenshot_prompt_regressions_are_synthesized`
- `.venv/bin/python -m pytest tests/test_answer_intent_classifier.py`
- `.venv/bin/python -m pytest tests/test_answer_eval.py`
- `.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py`
- `.venv/bin/python -m pytest tests/test_fretboard_examples.py`
- Question-bank classifier validation: 264 rows, 0 failures
- `.venv/bin/python -m pytest`
- `git diff --check`

Results:

- Focused screenshot regression tests: 2 passed
- Answer intent classifier: 62 passed
- Answer eval: 9 passed
- API contract/search/full answer quality: 234 passed
- Fretboard examples: 43 passed
- Full pytest: 659 passed
- `git diff --check`: passed

## Retrieval Gating

Retrieval gating remains intact. This slice did not change off-domain or unsafe/impossible guardrail behavior.

## Public/API Shape

No public `/api/answer` response schema changes were made.

## Risks

- The broader repo remains dirty with many unrelated parked files. Repo Steward should stage only the safe-to-stage list below.
- This is a narrow teacher-first slice, not the full future teacher-first composer. More prompt families may still need curated/template handling.
- `1-4-5-1 turnaround` currently uses G as the default example when no key is supplied. That is intentional for this slice, but future work could ask for key or infer from context.

## Safe-To-Stage List

- `pocketsteel/fretboard_examples.py`
- `pocketsteel/curated_answers.py`
- `tests/test_fretboard_examples.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/teacher-first-answer-composer.md`

## Must Remain Unstaged

- UI files
- deployment files
- DNS/config/secrets
- Chroma/vector stores
- embeddings
- corpus-private/corpus-v2 generated data
- source-inbox data
- design assets
- unrelated parked docs/tests/scripts shown by `git status --short`

## Exact Next QA Prompt For Lane 15

Please QA the teacher-first backend slice on `feature/answer-api`.

Review `docs/handoffs/task-completions/teacher-first-answer-composer.md`, then run the screenshot-derived prompts:

1. `How do I play a G-minor chord?`
2. `How do I play a 1-4-5-1 turnaround?`
3. `What’s it mean for a song to be a swing or a waltz?`

Also rerun the 12-prompt smoke set and confirm:

- primary answers are synthesized teaching content, not forum fragments
- source cards remain evidence below the answer where expected
- deterministic chord/fretboard answers remain source-free
- non-position prompts do not attach fretboard
- off-domain/unsafe retrieval gating still blocks retrieval
- no `[object Object]`
- no weak-source warning as primary answer

## QA Readiness

Ready for Lane 15 QA re-review.
