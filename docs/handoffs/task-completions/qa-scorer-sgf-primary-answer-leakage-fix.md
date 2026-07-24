# QA Scorer SGF Primary Answer Leakage Fix

Generated: 2026-06-14 15:23 America/Chicago

## Task Summary

Requested: update the broad answer-quality evaluator so it hard-fails obvious SGF/forum snippet leakage that manual user smoke found but the previous scorer over-reported as passing.

Completed:

- Hardened the QA scorer in `scripts/run_full_answer_quality_eval.py`.
- Added focused regression tests in `tests/test_full_answer_quality_eval.py`.
- Ran focused evaluator tests and the available full answer-quality eval path after the latest Lane 05 fixes.

Intentionally not changed:

- Backend product behavior, answer routing, answer composer logic, retrieval, Chroma/vector stores, corpus data, embeddings, scraping, deployment, DNS, auth, UI, staging, and commits.

## Repo State

- Branch: `feature/answer-api`
- Current HEAD during this QA task: `6a5f978`
- Note: the earlier broad QA matrix artifacts were generated at `a9eaa82`; current HEAD includes later Lane 05/backend and Lane 06/UI commits.
- Dirty worktree existed before this task and includes many unrelated parked files. This QA slice only changed the scorer/test files listed below plus this handoff.

## Files Changed

- `scripts/run_full_answer_quality_eval.py`
- `tests/test_full_answer_quality_eval.py`
- `docs/handoffs/task-completions/qa-scorer-sgf-primary-answer-leakage-fix.md`

## Scorer Rules Added

New hard-fail or warning coverage:

- `sgf_primary_answer_leakage`: answer body appears copied from retrieved SGF/forum snippets.
- `forum_first_person_fragment_leakage`: forum-like first-person fragments appear in the answer body.
- `deterministic_teacher_answer_source_fragment`: deterministic or teacher prompts are answered with source fragments.
- `weak_source_boilerplate_in_answer`: weak-source boilerplate appears in answer text; fails when it replaces the answer, warns when secondary.
- `off_domain_sgf_source_cards`: off-domain/guardrail answer returns SGF source cards.
- `lesson_request_without_lesson`: lesson request does not provide an actual lesson.
- `scale_request_missing_notes`: scale request does not name the scale notes.
- `lick_request_without_playable_lick`: lick/tab request does not provide playable lick/tab content.
- `song_title_unrelated_theory_fragments`: song/title question is answered with unrelated theory fragments.
- `repair_instruction_source_fragment_failure`: repair/instruction question is answered with unrelated source fragments.

## Golden Regression Rows Covered

The focused tests cover the requested user-smoke failures:

- `Give me the longest response you can.`
- `Show me the major scale in G`
- `Show me A minor and C major chords.`
- `give me a real lesson now`
- `Can I make a steel guitar rag with a regular rag?`
- `Can I fart on a steel guitar?`
- `Has anyone died playing pedal steel?`
- `show me 1 real lick, no words, just a lick.`
- `teach me something i don't already know`
- `What key is "over the rainbow" written in?`

## Tests And Checks

Passed:

```bash
.venv/bin/python -m pytest tests/test_full_answer_quality_eval.py -q
# 55 passed in 0.31s

.venv/bin/python -m pytest tests/test_answer_eval.py tests/test_full_answer_quality_eval.py -q
# 64 passed in 0.30s

git diff --check
# passed
```

Available full answer-quality eval rerun:

```bash
.venv/bin/python scripts/run_full_answer_quality_eval.py \
  --output /tmp/steel_guitar_rag-sgf-primary-scorer-full-eval.md \
  --json-output /tmp/steel_guitar_rag-sgf-primary-scorer-full-eval.json
```

Result:

- Total questions: `295`
- Pass: `130`
- Warn: `31`
- Fail: `134`
- Private source behavior correct: `true`
- Output artifacts: `/tmp/steel_guitar_rag-sgf-primary-scorer-full-eval.md`, `/tmp/steel_guitar_rag-sgf-primary-scorer-full-eval.json`

Important distinction: the previous 546-question broad matrix appears in repo as generated handoff/report artifacts, not as a standalone reusable script. I therefore reran the available persistent full answer-quality eval path and wrote outputs to `/tmp`.

## New Signal From Full Eval

Top new failure counts from the hardened scorer:

- `fail:sgf_primary_answer_leakage`: `85`
- `fail:forum_first_person_fragment_leakage`: `44`
- `fail:repair_instruction_source_fragment_failure`: `19`
- `fail:deterministic_teacher_answer_source_fragment`: `16`
- `fail:song_title_unrelated_theory_fragments`: `2`
- `fail:lick_request_without_playable_lick`: `1`

Example prompts now caught:

- `I want to slide from G at the 3rd fret to a higher G. Where should I go?`
- `What does A pedal and F lever give me?`
- `What does B+C give me?`
- `Where is the IV chord from open position?`
- `Why does my amp hum until I touch the changer?`

This high failure count is expected QA signal from the stricter scorer, not a runtime behavior change from this task.

## Integration Notes

- The scorer now treats raw SGF/forum text as a primary answer as a P1-style quality failure.
- Non-primary weak-source wording is still allowed as a warning, but primary weak-source boilerplate fails.
- Off-domain/guardrail answers with SGF source cards now fail.
- The scorer remains regex-based and intentionally conservative; future calibration may be needed after Lane 05 cleans up the newly visible failures.

## Risk Assessment

Risk: medium for QA noise, low for runtime.

- Runtime risk is low because only eval/test code changed.
- QA noise risk is medium because the new leakage detectors are intentionally aggressive and may need calibration for legitimate forum-quote requests or harmless source-card support.
- Rollback: revert the scorer/test changes in this slice if the new buckets prove too noisy.

## Commit Readiness

Commit readiness: `Safe to commit`

Safe-to-stage files for this QA slice:

- `scripts/run_full_answer_quality_eval.py`
- `tests/test_full_answer_quality_eval.py`
- `docs/handoffs/task-completions/qa-scorer-sgf-primary-answer-leakage-fix.md`

Files that must remain parked:

- Existing unrelated dirty files shown by `git status --short`, including corpus/source/provenance/design/deploy/static/UI/runtime changes not part of this scorer slice.
- `/tmp/steel_guitar_rag-sgf-primary-scorer-full-eval.md`
- `/tmp/steel_guitar_rag-sgf-primary-scorer-full-eval.json`

## Human Decision Needed

No for committing this QA scorer slice.

Future human/product judgment may be needed if the team wants to tune severity policy for source cards on edge-case guardrail or forum-wisdom prompts.

## Suggested Next Step

Recommended lane: `05 Backend / RAG Integration`

Exact prompt:

```text
Lane 05 Backend / RAG Integration: Use docs/handoffs/task-completions/qa-scorer-sgf-primary-answer-leakage-fix.md and the /tmp full answer-quality eval outputs to fix the highest-signal primary-answer leakage failures. Focus only on prompts now bucketed as sgf_primary_answer_leakage, forum_first_person_fragment_leakage, deterministic_teacher_answer_source_fragment, and repair_instruction_source_fragment_failure. Do not change Chroma, corpus, embeddings, scraping, deployment, DNS, auth, or UI. Add focused regression tests, run the required answer/API/eval suites, and write a handoff.
```
