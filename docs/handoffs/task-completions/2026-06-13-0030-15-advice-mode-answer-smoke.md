# Advice Mode Answer Smoke

## Task Summary
- Requested: add adversarial smoke/eval coverage for practical gear, gig, troubleshooting, and advice questions so raw forum fragments, jokes, anecdotes, weak-source wording, or background-only prose cannot pass as answers.
- Completed: verified loopback API reachability, added practical-advice prompts and failure buckets to QA/eval coverage, ran direct POST checks for the two real failures, reran exploratory smoke, and ran the requested checks plus full pytest.
- Intentionally not changed: no runtime answer behavior, Chroma stores, embeddings, `corpus-private`, `corpus-v2`, `source-inbox`, scraping, provenance/legal files, deployment secrets, `.wrangler`, DNS config, design assets, staging, commits, deployment, or DNS.

## Branch And HEAD
- Branch: `feature/answer-api`
- HEAD: `bad18d8`
- Prerequisite handoff expected: `docs/handoffs/task-completions/2026-06-13-*-05-answer-intent-mode-contract.md`
- Prerequisite handoff status: not found in `docs/handoffs/task-completions/` at run time.

## API Reachability Evidence
- `curl -sS -i http://127.0.0.1:8783/ | head -20 || true` returned `HTTP/1.0 200 OK`.
- `curl -sS -i http://127.0.0.1:8783/api/answer | head -20 || true` returned `HTTP/1.0 405 Method Not Allowed`, which is acceptable for GET `/api/answer` and confirms the local API was reachable.

## Prompts Added
- `How do people power their StroboPlus tuner when playing a gig? My batteries run out very fast.`
- `I broke a string during a show. Has that happened to anyone else? What do people do?`
- `My 3rd string keeps breaking at gigs. What should I carry?`
- `What should be in a pedal steel emergency gig kit?`
- `My amp hums until I touch the changer. What should I check first?`
- `Should delay go before my volume pedal or after it?`
- `What do players say about breaking strings on stage?`
- `Do steel players use battery-powered tuners live?`
- Existing sentinels remain covered: `What's a G chord even mean?` and `Is 5-7-8 with E lowered a B9 pocket?`

## Buckets Added
- `advice_question_must_answer_directly`
- `advice_question_raw_fragment_failure`
- `advice_question_joke_anecdote_failure`
- `gear_question_background_only_failure`
- `deterministic_visual_missing_fretboard`
- `weak_source_leakage`
- `object_object_rendering`

## Direct POST Results
Both direct checks returned HTTP 200 and were classified as hard product failures.

| Prompt | Outcome | Buckets |
| --- | --- | --- |
| `How do people power their StroboPlus tuner when playing a gig? My batteries run out very fast.` | Fail | `advice_question_must_answer_directly` |
| `I broke a string during a show. Has that happened to anyone else? What do people do?` | Fail | `advice_question_must_answer_directly`, `advice_question_raw_fragment_failure`, `advice_question_joke_anecdote_failure` |

## Exploratory Smoke
- Command used:

```bash
.venv/bin/python scripts/run_exploratory_answer_smoke.py \
  --base-url http://127.0.0.1:8783 \
  --output /tmp/steel_guitar_rag-advice-mode-answer-smoke.md \
  --json-output /tmp/steel_guitar_rag-advice-mode-answer-smoke.json
```

- Output artifacts:
  - `/tmp/steel_guitar_rag-advice-mode-answer-smoke.md`
  - `/tmp/steel_guitar_rag-advice-mode-answer-smoke.json`
- Note: outputs were written to `/tmp` to avoid touching `corpus-private` or `corpus-v2`.

## Smoke Totals
- Total prompts: 193
- Pass: 100
- Warn: 80
- Fail: 13

## Failures By Prompt And Bucket
- `What's a G chord even mean?`
  - `chord_position_missing_fretboard`
  - `deterministic_answer_has_sources`
  - `chord_position_has_sgf_source_cards`
  - `chord_position_missing_expected_frets`
  - `beginner_chord_concept_router_escape`
- `What does a C chord mean?`
  - `chord_position_missing_fretboard`
  - `deterministic_answer_has_sources`
  - `chord_position_has_sgf_source_cards`
  - `chord_position_missing_expected_frets`
  - `beginner_chord_concept_router_escape`
- `What notes are in a D chord?`
  - `chord_position_missing_fretboard`
  - `deterministic_answer_has_sources`
  - `chord_position_has_sgf_source_cards`
  - `chord_position_missing_expected_frets`
  - `beginner_chord_concept_router_escape`
- `Where is a G chord?`
  - `chord_position_missing_fretboard`
  - `deterministic_answer_has_sources`
  - `chord_position_has_sgf_source_cards`
  - `chord_position_missing_expected_frets`
  - `beginner_chord_concept_router_escape`
- `How do I play G on E9?`
  - `chord_position_missing_fretboard`
  - `deterministic_answer_has_sources`
  - `chord_position_has_sgf_source_cards`
  - `chord_position_missing_expected_frets`
  - `beginner_chord_concept_router_escape`
- `What makes an E minor chord minor?`
  - `deterministic_visual_missing_fretboard`
  - `deterministic_answer_has_sources`
  - `beginner_chord_concept_router_escape`
- `How do people power their StroboPlus tuner when playing a gig? My batteries run out very fast.`
  - `advice_question_must_answer_directly`
- `I broke a string during a show. Has that happened to anyone else? What do people do?`
  - `advice_question_must_answer_directly`
  - `advice_question_raw_fragment_failure`
  - `advice_question_joke_anecdote_failure`
- `My 3rd string keeps breaking at gigs. What should I carry?`
  - `advice_question_must_answer_directly`
  - `advice_question_raw_fragment_failure`
- `What should be in a pedal steel emergency gig kit?`
  - `advice_question_must_answer_directly`
  - `advice_question_raw_fragment_failure`
- `Should delay go before my volume pedal or after it?`
  - `advice_question_must_answer_directly`
  - `advice_question_raw_fragment_failure`
  - `gear_question_background_only_failure`
- `What do players say about breaking strings on stage?`
  - `advice_question_must_answer_directly`
  - `advice_question_raw_fragment_failure`
- `Do steel players use battery-powered tuners live?`
  - `advice_question_must_answer_directly`
  - `advice_question_raw_fragment_failure`

## Warning Clusters
- `warn:source_excerpt_unrelated`: 218
- `warn:source_excerpt_too_short`: 37
- `warn:low_teaching_value`: 8

## Tests And Checks
- `git diff --check` - passed.
- `.venv/bin/python -m pytest tests/test_answer_eval.py tests/test_full_answer_quality_eval.py` - passed, `50 passed`.
- `.venv/bin/python -m pytest tests/test_api_search.py tests/test_fretboard_examples.py` - passed, `201 passed`.
- `.venv/bin/python -m pytest` - passed, `546 passed`.
- Final `git diff --check` - passed.

## Files Changed
- Changed tracked files:
  - `scripts/run_full_answer_quality_eval.py`
  - `tests/fixtures/user_question_bank.json`
  - `tests/test_full_answer_quality_eval.py`
- Existing untracked QA files with current-task edits:
  - `scripts/run_exploratory_answer_smoke.py`
  - `tests/test_exploratory_answer_smoke.py`
- Created:
  - `docs/handoffs/task-completions/2026-06-13-0030-15-advice-mode-answer-smoke.md`
- Deleted files:
  - None.
- Generated artifacts:
  - `/tmp/steel_guitar_rag-advice-mode-answer-smoke.md`
  - `/tmp/steel_guitar_rag-advice-mode-answer-smoke.json`

## Integration Notes
- This is a real product failure, not an environment/setup issue. The local API was reachable.
- The practical advice failures show the answer stack still lets fragment-style forum content through for gig and troubleshooting questions.
- The StroboPlus power answer gives generic tuner background and does not answer the battery/power problem.
- The broken-string and emergency-kit style answers include raw bullet fragments, anecdotes, and joke/injury-story content.
- `integration-status.md` should be refreshed to show this QA lane as blocked by practical advice mode failures.
- The missing Lane 05 prerequisite handoff should be resolved or superseded by the next backend handoff.

## Risk Assessment
- Risk: Low for this QA change.
- Why: changes are confined to eval/smoke scripts, tests, fixtures, and this handoff. No runtime answer behavior or data stores were modified.
- Rollback: revert the QA/eval changes and this handoff if Lane 05 chooses different bucket names or fixture placement.

## Commit Readiness
- Not ready to commit.

The tests are green, but live exploratory smoke exposed 13 hard product failures, including 7 practical advice failures. Commit should wait for Lane 05 to implement or confirm the advice intent/mode route, then Lane 15 should rerun this smoke.

## Suggested Next Step
- Recommended lane: `05 Backend / RAG Integration`.
- Suggested prompt: implement answer intent/mode handling for practical advice questions so gear/gig/troubleshooting answers synthesize direct practical steps before using sources as support. At minimum, fix StroboPlus gig power/battery questions, broken-string-on-stage questions, repeated 3rd-string breakage, emergency gig kit, delay placement, and battery-powered tuner questions so they avoid raw snippets, jokes, anecdotes, weak-source wording, and background-only answers.

## Current Status
- QA coverage has been added and passes locally.
- Exploratory smoke now catches practical advice failures.
- Product status: blocked until practical advice questions route to direct synthesized answers.

## Remaining Blockers
- Seven live loopback practical advice prompts still fail hard.
- Six prior beginner chord concept prompts still fail hard.
- Expected Lane 05 answer-intent/mode handoff was not present.

## Recommended Next Lane
- `05 Backend / RAG Integration` to implement the practical advice answer mode/intent route.
