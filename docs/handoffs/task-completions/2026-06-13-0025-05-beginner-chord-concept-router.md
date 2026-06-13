# Beginner Chord Concept Router

## Task summary
- Requested: fix beginner/basic chord-concept routing so questions like `What's a G chord even mean?` produce deterministic, fretboard-backed answers instead of SGF/forum fragment synthesis.
- Completed:
  - Added deterministic chord-concept parsing for major/minor chord meaning and chord-spelling prompts.
  - Reused the existing pitch-math fretboard engine for concrete chord concepts.
  - Added broader major-position phrasing support for `Where is a G chord?`, `Show me a G chord`, and `How do I play G on E9?`.
  - Added deterministic no-source concept fallbacks for generic beginner questions without a concrete chord/root.
  - Updated answer-quality smoke/eval heuristics so clean `F#` and `lowered the third` wording pass the beginner chord-concept checks.
- Intentionally not changed: deployment, DNS, commits, staging, Chroma/vector stores, embeddings, `corpus-private`, `corpus-v2`, `source-inbox`, scraping, provenance/legal files, deployment secrets, `.wrangler`, auth, DNS config, and design assets.

## Branch and HEAD
- Branch: `feature/answer-api`
- HEAD: `bad18d8`
- Worktree: dirty before this task with many unrelated modified/untracked lane files. This task did not stage or commit anything.

## Root cause
- Bucket: C. deterministic chord router miss.
- Details:
  - The deterministic router already caught many location prompts like `Where can I play a G chord?`.
  - It did not catch beginner concept forms such as `What's a G chord even mean?`, `What does a C chord mean?`, or `What notes are in a D chord?`.
  - Those prompts could fall through to retrieval/forum synthesis, creating loose fragment-style answers with no chord tones, no E9 application, and no `response.fretboard`.
  - The response builder did not strip fretboard data; the route simply did not produce deterministic fretboard data for this intent.

## Route/fallback path before fix
- Prompt: `What's a G chord even mean?`
- Previous behavior observed in protected/local UI:
  - loose forum-like bullet fragments,
  - no clear `G-B-D` explanation,
  - no root/3rd/5th explanation,
  - no E9 position explanation,
  - no top-level `response.fretboard`,
  - no `response.fretboard.positions`.

## Behavior after fix
- Prompt: `What's a G chord even mean?`
- In-process `/api/answer` verification:
  - Answer:
    ```text
    A G major chord means the notes G-B-D: root, major 3rd, and perfect 5th.

    On E9, common G major starter positions include:
    - 3rd fret with no pedals: Open position, grip 4-5-6.
    - 6th fret with A + F: A+F position, grip 4-5-6.
    - 10th fret with A + B: A+B position, grip 4-5-6.

    Think of the chord name as the target sound; the fretboard positions are different ways to spell the same root-3rd-5th idea on the steel.
    ```
  - `sources`: `0`
  - `warnings`: `[]`
  - `response.fretboard.title`: `G major positions on E9`
  - visible position ids: `g-open-3`, `g-af-6`, `g-ab-10`
  - total positions: `44`

## Prompts covered
- `What's a G chord even mean?`
- `What does a C chord mean?`
- `What notes are in a D chord?`
- `Where is a G chord?`
- `How do I play G on E9?`
- `Show me a G chord`
- `What makes an E minor chord minor?`
- `What is the vi chord in G?`
- Generic no-root concept fallbacks:
  - `What makes something a minor chord?`
  - `What is a 1 chord?`
  - `Why is A+B a chord?`

## Files changed
- Changed files:
  - `pocketsteel/fretboard_examples.py`
  - `pocketsteel/curated_answers.py`
  - `scripts/run_full_answer_quality_eval.py`
  - `scripts/run_exploratory_answer_smoke.py`
  - `tests/test_fretboard_examples.py`
  - `tests/test_api_search.py`
- Created files:
  - `docs/handoffs/task-completions/2026-06-13-0025-05-beginner-chord-concept-router.md`
- Deleted files: none.
- Generated artifacts: none.

## Tests and checks
- Command:
  - `.venv/bin/python -m pytest tests/test_fretboard_examples.py tests/test_api_search.py tests/test_api_contract.py`
- Result:
  - `198 passed in 0.50s`
- Command:
  - `.venv/bin/python -m pytest tests/test_answer_eval.py tests/test_full_answer_quality_eval.py`
- Result:
  - `43 passed in 0.20s`
- Additional eval-harness command after heuristic alignment:
  - `.venv/bin/python -m pytest tests/test_answer_eval.py tests/test_full_answer_quality_eval.py tests/test_exploratory_answer_smoke.py`
- Result:
  - `62 passed in 0.26s`
- Command:
  - `.venv/bin/python -m pytest`
- Result:
  - `531 passed in 4.20s`
- Command:
  - `git diff --check`
- Result:
  - passed with no whitespace errors.

## Tests added/updated
- `tests/test_fretboard_examples.py`
  - Added parser/payload coverage for beginner chord-concept prompts.
- `tests/test_api_search.py`
  - Added end-to-end `/api/answer` coverage proving deterministic answers, correct chord tones, E9 application, fretboard payloads, source suppression, warning suppression, and no `[object Object]`.
- `scripts/run_full_answer_quality_eval.py`
  - Updated beginner chord-concept heuristic for sharp-note matching and minor-third wording.
- `scripts/run_exploratory_answer_smoke.py`
  - Updated beginner chord-concept heuristic for sharp-note matching.

## Integration notes
- Concrete major chord-concept prompts now return major-position fretboard payloads.
- Concrete minor chord-concept prompts now return pitch-validated minor-position payloads.
- Generic concept prompts without a concrete chord/root return deterministic source-free text and no fretboard payload.
- `response.fretboard.positions` remains the primary frontend contract.
- No raw UI geometry is emitted.
- No SGF source cards or weak-source warnings are returned for deterministic chord/theory answers.
- `scripts/run_exploratory_answer_smoke.py` was already untracked in this worktree before this task. This task made a small heuristic edit inside it, so staging that file should be coordinated with the QA lane.

## Protected-preview / QA follow-up
- Lane 15 should rerun exploratory answer smoke after restarting the loopback API from the current worktree.
- Protected-preview smoke should include:
  - `What's a G chord even mean?`
  - `What does a C chord mean?`
  - `What notes are in a D chord?`
  - `What makes an E minor chord minor?`
  - `What is the vi chord in G?`

## Safe-to-stage file list
- `pocketsteel/fretboard_examples.py`
- `pocketsteel/curated_answers.py`
- `scripts/run_full_answer_quality_eval.py`
- `tests/test_fretboard_examples.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-13-0025-05-beginner-chord-concept-router.md`
- `scripts/run_exploratory_answer_smoke.py` only if the QA lane confirms the existing untracked smoke-runner file should be included in this commit scope.

## Files that must remain unstaged
- `corpus-private/**`
- `corpus-v2/**`
- `source-inbox/**`
- Chroma/vector-store files
- embeddings
- scraper outputs
- provenance/legal source dumps
- deployment secrets
- `.wrangler/**`
- DNS/tunnel/app config
- design assets
- unrelated dirty worktree files from other lanes

## Risk assessment
- Low to medium.
- Low because the runtime change is scoped to deterministic parser/answer helpers and existing payload builders.
- Medium only for commit coordination because one touched QA smoke-runner file is currently untracked and pre-existing from another lane.
- Rollback notes:
  - Revert the chord-concept helper additions in `pocketsteel/fretboard_examples.py`, the curated import/route in `pocketsteel/curated_answers.py`, and the associated tests/eval heuristic updates.

## Commit readiness
Needs human review first

Reason: implementation and tests are green, but `scripts/run_exploratory_answer_smoke.py` is an existing untracked QA-lane file. Decide whether to include that file in the backend commit scope or coordinate a QA-lane commit.

## Suggested next step
- Recommended next lane: Lane 15 QA / Answer Eval.
- Exact recommended task:
  - "Restart the loopback API from the current worktree and rerun exploratory answer smoke, including beginner chord-concept prompts. Confirm `What's a G chord even mean?` returns `G-B-D`, E9 positions, `response.fretboard.positions`, `sources: []`, and no weak-source warning."
