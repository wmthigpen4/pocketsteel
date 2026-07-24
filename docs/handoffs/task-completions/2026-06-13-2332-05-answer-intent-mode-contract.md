## Task summary
- Requested: add a deterministic intent-mode answer contract so practical advice questions produce useful synthesized guidance instead of raw forum fragments.
- Completed: added `intent_mode` classification for `instrument_visual`, `gear_advice`, `gig_advice`, `forum_wisdom`, `lesson_navigation`, `tab_explainer`, `history_player_context`, and `unknown_low_confidence`; added source-free curated practical answers for StroboPlus gig power, delay/volume-pedal order, battery-powered live tuners, broken strings at gigs, emergency gig kit, and synthesized string-break forum wisdom.
- Completed: wired the practical intent-mode answer path into `/api/answer` after deterministic fretboard answers and before retrieval.
- Completed: added explicit `gear_advice`, `gig_advice`, and `forum_wisdom` answer contracts with source-fragment hygiene.
- Completed: added API/contract tests covering the high-risk practical advice prompts and regressions for deterministic fretboard answers.
- Intentionally not changed: no retrieval ranking, Chroma/vector data, embeddings, scraping, corpus data, auth, deployment, DNS, frontend UI, or `/api/answer` public response shape.

## Root cause
- Practical advice questions were being handled by either generic curated definitions or retrieval-shaped synthesis.
- For questions such as StroboPlus gig power, the existing high-confidence product definition could answer what the product is while missing the user's power problem.
- For show/gig string break questions, source snippets could be noisy anecdotes; the answer layer needed a pre-retrieval practical mode to synthesize the useful action plan first.

## Behavior before/after
- StroboPlus prompt: `How do people power their StroboPlus tuner when playing a gig? My batteries run out very fast.`
  - Before: could lead with product-definition style text such as `A Peterson StroboPlus is...` or source-shaped fragments.
  - After: starts with `Short answer: treat the tuner power source as part of your gig rig, not an afterthought.` It tells the user to check the exact model/manual, use only supported external USB/power behavior, start with fresh batteries or full charge, carry spare batteries, and keep a backup tuner.
- Broken-string prompt: `I broke a string during a show. Has that happened to anyone else? What do people do?`
  - Before: could surface anecdote/joke/embarrassment/injury fragments.
  - After: starts with `Short answer: yes, strings break on stage; plan for recovery, not panic.` It tells the user to stay calm, finish if possible, shift grips/positions, use backup instrument if available, change at set break, carry spare strings/cutters/winder/tuner/light, and inspect burrs/gauge/winding/travel.

## Intent modes
- `instrument_visual`: deterministic fretboard/chord answers. These still run first, stay source-free, and keep `response.fretboard.positions`.
- `gear_advice`: practical rig/gear setup answers, currently StroboPlus power, delay placement, and live battery tuner questions.
- `gig_advice`: practical show-recovery answers, currently broken strings and emergency gig kit.
- `forum_wisdom`: synthesized consensus/takeaway, currently stage string-break discussion.
- `lesson_navigation`, `tab_explainer`, `history_player_context`, `unknown_low_confidence`: classifier modes added for future routing; no broad runtime behavior was added for them in this task.

## Answer-shape and source-hygiene rules
- Advice answers start with a short synthesized answer.
- Advice answers include practical steps.
- Gear advice includes what to check before buying/changing anything.
- Forum wisdom is synthesized as player takeaway rather than copied anecdote.
- Joke, injury, gore, embarrassment, `Top`, email/contact, and raw forum fragments are forbidden by the relevant contracts.
- Advice-mode early answers currently return `sources: []` and `warnings: []`; source cards can be added later only when they cleanly support the practical answer.

## Files changed
- Changed files:
  - `steel_guitar_rag/api.py`
  - `steel_guitar_rag/curated_answers.py`
  - `steel_guitar_rag/answer_contracts.py`
  - `tests/test_api_search.py`
  - `tests/test_full_answer_quality_eval.py`
- Created files:
  - `docs/handoffs/task-completions/2026-06-13-2332-05-answer-intent-mode-contract.md`
- Deleted files: none.
- Generated artifacts: none.

## Tests and checks
- `.venv/bin/python -m pytest tests/test_api_search.py tests/test_api_contract.py tests/test_answer_eval.py tests/test_full_answer_quality_eval.py`
  - Result: `218 passed in 0.73s`
- `.venv/bin/python -m pytest tests/test_fretboard_examples.py`
  - Result: `37 passed in 0.16s`
- `.venv/bin/python -m pytest`
  - Result: `546 passed in 4.12s`
- `git diff --check`
  - Result: passed with no output.
- Tests skipped: none.

## Integration notes
- `/api/answer` now has this order:
  1. deterministic fretboard/chord route;
  2. practical intent-mode route;
  3. retrieval/sanitization/curated/provider fallback.
- Public API shape is unchanged. No `intent_mode` field is exposed.
- Deterministic fretboard answers still suppress top-level source cards and attach fretboard payloads where visualizable.
- Practical advice answers intentionally do not get fretboard payloads.
- Assumption: source-free curated advice is acceptable for the initial high-risk failures; later work can add clean supporting source cards below the synthesized advice.
- Blockers: none for this task slice.
- Human decisions needed: decide whether future `gear_advice` and `gig_advice` answers should show clean supporting source cards when available, or remain source-free curated guidance.

## Smoke recommendations
- Lane 15 should include these prompts in the next exploratory smoke:
  - `How do people power their StroboPlus tuner when playing a gig? My batteries run out very fast.`
  - `I broke a string during a show. Has that happened to anyone else? What do people do?`
  - `Should delay go before my volume pedal or after it?`
  - `My 3rd string keeps breaking at gigs. What should I carry?`
  - `What should be in a pedal steel emergency gig kit?`
  - `What do players say about breaking strings on stage?`
  - `Do steel players use battery-powered tuners live?`
- Protected-preview smoke should verify that these answers have no fretboard visualization and no raw SGF anecdote fragments.

## Risk assessment
- Risk: Low to Medium.
- Why: the runtime change is a narrow early answer route, but it changes answer behavior before retrieval for a class of gear/gig prompts.
- Rollback notes: remove the `intent_mode_curated_answer(...)` early return from `steel_guitar_rag/api.py`; the helper/contracts/tests can remain inert or be removed in a follow-up.

## Commit readiness
- Needs human review first.
- Reason: this task slice is fully test-green, but the worktree contains many unrelated modified/untracked files from other lanes. Do not stage the whole worktree.
- Exact safe-to-stage file list for this task after review:
  - `steel_guitar_rag/api.py`
  - `steel_guitar_rag/curated_answers.py`
  - `steel_guitar_rag/answer_contracts.py`
  - `tests/test_api_search.py`
  - `tests/test_full_answer_quality_eval.py`
  - `docs/handoffs/task-completions/2026-06-13-2332-05-answer-intent-mode-contract.md`
- Must remain unstaged unless separately approved:
  - Chroma/vector stores, embeddings, `corpus-private/`, `corpus-v2/`, `source-inbox/`, generated reports, deployment secrets/config, `.wrangler`, DNS config, design assets, and any unrelated dirty worktree files.

## Suggested next step
- Lane 15 QA / Answer Eval should rerun exploratory answer smoke against the protected-preview loopback and confirm the practical advice cluster is no longer returning forum fragments.
- Suggested prompt: `Rerun exploratory answer smoke for gear_advice/gig_advice/forum_wisdom practical advice prompts and report any remaining source-fragment leakage.`
