# SGF Answer Quarantine And General Teacher Router Fix

## Task Summary
- Request: fix user-smoke failures where SGF/forum fragments became the primary answer body for ordinary questions.
- Completed: added source-free teacher routes for the reported smoke prompts, added a final SGF answer-body quarantine before `/api/answer` returns, expanded answer-contract/quality forbidden patterns, and added a combined A minor / C major fretboard payload.
- Intentionally not changed: UI rendering, source-card layout, auth, deployment, DNS, corpus, Chroma/vector stores, embeddings, scraping, private/source-inbox data, and design assets.

## Root Cause
Fallback answer synthesis could still allow retrieved SGF/forum text, or lightly cleaned versions of it, to become the answer body when no deterministic teacher route caught the prompt. Some broad but answerable prompts also had no source-free teacher route, so unrelated SGF fragments looked like the product answer.

## Files Changed
- `steel_guitar_rag/curated_answers.py`
- `steel_guitar_rag/api.py`
- `steel_guitar_rag/answering.py`
- `steel_guitar_rag/answer_contracts.py`
- `steel_guitar_rag/fretboard_examples.py`
- `tests/test_api_search.py`
- `tests/test_fretboard_examples.py`
- `docs/handoffs/task-completions/sgf-answer-quarantine-teacher-router-fix.md`

## Behavior Added
- Added `sgf_quarantine_teacher_answer(...)` source-free routes for:
  - underspecified “longest response” requests
  - G major scale
  - A minor plus C major
  - “real lesson now”
  - “Steel Guitar Rag” / cloth rag pun
  - harmless off-color prompt
  - morbid pedal-steel safety prompt
  - no-words lick request
  - “teach me something”
  - “Over the Rainbow” key
  - Steel Guitar Rag title/writer/key/play/app-name questions
  - noisy volume pedal
  - tuning instability
  - repair-person lookup needing current directory/web context
- Added final API quarantine: if raw provider output or final answer contains known SGF/forum fragment markers, discard it, return a teacher fallback, and suppress sources/warnings.
- Added A minor / C major combined fretboard payload using existing pitch-validated position builders.

## Before / After Examples
- `Give me the longest response you can.`
  - Before: SGF fragment about “you desire more information” plus weak-source wording.
  - After: starts `I can give a detailed steel-guitar lesson, but I need a topic...`; sources `[]`.
- `Show me the major scale in G`
  - Before: generic/weak-source answer, missing direct scale.
  - After: starts `G major is G A B C D E F# G.`; sources `[]`.
- `Show me A minor and C major chords.`
  - Before: SGF/tab fragments.
  - After: starts `A minor = A-C-E. C major = C-E-G.` and includes a combined fretboard payload.
- `give me a real lesson now`
  - Before: forum fragments about students.
  - After: starts `Lesson: find I-to-IV movement on E9.`; sources `[]`.
- `Can I make a steel guitar rag with a regular rag?`
  - Before: unrelated build fragments.
  - After: cloth rag no; ragtime tune yes.
- `Can I fart on a steel guitar?`
  - Before: SGF fragments.
  - After: direct harmless answer; no retrieval evidence.
- `Has anyone died playing pedal steel?`
  - Before: forum fragments about age/playing.
  - After: no reliable evidence of death caused by playing; safety risks listed.
- `show me 1 real lick, no words, just a lick.`
  - Before: forum fragments about licks.
  - After: small E9 lick block only.
- `teach me something i don't already know`
  - Before: forum fragments.
  - After: concise E9 position-family concept.
- `What key is "over the rainbow" written in?`
  - Before: unrelated theory fragments.
  - After: common Wizard of Oz reference key E-flat major with arrangement caveat.

## Tests And Checks
- `git status --short`: worktree has many unrelated parked files; scoped changed files listed above.
- `git diff --check`: passed.
- `python3 -m py_compile steel_guitar_rag/curated_answers.py steel_guitar_rag/api.py steel_guitar_rag/answering.py steel_guitar_rag/answer_contracts.py steel_guitar_rag/fretboard_examples.py`: passed.
- `.venv/bin/python -m pytest tests/test_api_search.py -k "sgf_quarantine or mixed_a_minor or off_domain_user_smoke"`: `3 passed`.
- `.venv/bin/python -m pytest tests/test_fretboard_examples.py -k "mixed_a_minor"`: `1 passed`.
- `.venv/bin/python -m pytest tests/test_answer_intent_classifier.py`: `70 passed`.
- `.venv/bin/python -m pytest tests/test_answer_eval.py`: `9 passed`.
- `.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py`: `274 passed`.
- `.venv/bin/python -m pytest tests/test_fretboard_examples.py`: `52 passed`.
- Exact user-smoke prompt API rerun: all 16 prompts returned direct teacher/guardrail answers with `sources=[]`, `warnings=[]`; A minor/C major included `fretboard`.
- `.venv/bin/python -m pytest`: `668 passed, 2 failed`.
  - Known unrelated failures:
    - `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`
    - `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`
- Broad QA matrix rerun: not run; focused exact prompt rerun and full pytest were run instead.

## Smoke Target
- Target type: API-fallback
- Result type: API fallback, not browser smoke
- Exact browser URL tested: not run
- Cache-busted URL tested: not run
- Exact URL the user should use: protected preview URL after Lane 12 restarts/verifies current HEAD
- Auth required: not applicable for local test helper
- Auth provider: not applicable
- Cloudflare Access login result: not attempted
- Local backend URL: in-process WSGI test helper, not a running server
- Expected backend port: not applicable
- Expected git HEAD: current working tree after this patch
- Version endpoint: not queried
- Version endpoint result: not queried
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: yes in protected preview, outside this backend slice
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes in protected preview, outside this backend slice
- Who should test this URL: Lane 12 / user after restart
- Do not test these URLs: raw corpus/vector/private paths
- Known caveats: browser smoke was not run in this backend task; full pytest still has the two known unrelated static/UI failures.

## Risk Assessment
- Risk: medium-low.
- Why: changes touch shared answer routing and final answer cleanup, but are restricted to known fragment quarantine and deterministic teacher routes; source cards are suppressed only for quarantined/deterministic answers.
- Rollback: revert this commit/slice to restore previous answer fallback behavior.

## Commit Readiness
Safe to commit.

Safe-to-stage files:
- `steel_guitar_rag/curated_answers.py`
- `steel_guitar_rag/api.py`
- `steel_guitar_rag/answering.py`
- `steel_guitar_rag/answer_contracts.py`
- `steel_guitar_rag/fretboard_examples.py`
- `tests/test_api_search.py`
- `tests/test_fretboard_examples.py`
- `docs/handoffs/task-completions/sgf-answer-quarantine-teacher-router-fix.md`

Must remain unstaged:
- unrelated parked docs, corpus metadata, deployment/landing files, generated reports, `source-inbox/`, `corpus-private/`, `corpus-v2/`, UI/design assets, and all untracked work not listed above.

## Suggested Next Step
Lane 12 protected-preview verification:

```text
Read docs/handoffs/task-completions/sgf-answer-quarantine-teacher-router-fix.md and integration-status.md. Restart protected preview on the approved backend command, verify /api/version HEAD, and browser-smoke the exact SGF quarantine prompt set. Confirm source cards are absent for deterministic teacher answers and that user smoke may continue.
```
