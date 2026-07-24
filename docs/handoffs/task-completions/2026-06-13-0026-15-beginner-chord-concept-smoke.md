# Beginner Chord Concept Smoke

## Task Summary
- Requested: add and run smoke/eval coverage for vague beginner chord/theory prompts so they cannot silently fall back to retrieval/forum fragments.
- Completed: verified the loopback API was reachable, ran direct POST checks for the requested prompts, added QA/eval fixture coverage and failure classification, reran exploratory smoke, and ran the requested tests plus full pytest.
- Intentionally not changed: no runtime answer behavior, Chroma stores, embeddings, `corpus-private`, `corpus-v2`, `source-inbox`, scraping, provenance/legal files, deployment secrets, `.wrangler`, DNS config, design assets, staging, commits, deployment, or DNS.

## Branch And HEAD
- Branch: `feature/answer-api`
- HEAD: `bad18d8`
- Prerequisite handoff expected: `docs/handoffs/task-completions/2026-06-13-*-05-beginner-chord-concept-router.md`
- Prerequisite handoff status: not found in `docs/handoffs/task-completions/` at run time.

## API Reachability Evidence
- `curl -sS -i http://127.0.0.1:8783/ | head -20 || true` returned `HTTP/1.0 200 OK`.
- `curl -sS -i http://127.0.0.1:8783/api/answer | head -20 || true` returned `HTTP/1.0 405 Method Not Allowed`, which is acceptable for GET `/api/answer` and confirms the local API was reachable.

## Direct POST Results
All direct checks returned HTTP 200 and no `[object Object]`. Product behavior still fails for six of seven requested prompts.

| Prompt | Result | Notes |
| --- | --- | --- |
| `What's a G chord even mean?` | Fail | No fretboard payload, source cards returned, loose SGF-style fragments. |
| `What does a C chord mean?` | Fail | No fretboard payload, source cards returned, loose theory/source fragments. |
| `What notes are in a D chord?` | Fail | No fretboard payload, source cards returned, unrelated C-triad fragments. |
| `Where is a G chord?` | Fail | No fretboard payload, source cards returned, raw G/E minor forum fragments. |
| `How do I play G on E9?` | Fail | No fretboard payload, source cards returned, loose E9/G6/C6 fragments. |
| `What makes an E minor chord minor?` | Fail | No fretboard payload, source cards returned, fragment answer instead of beginner theory plus visual. |
| `What is the vi chord in G?` | Pass | Deterministic, source-free, visual fretboard payload present. |

## QA Coverage Added
- Added failure bucket: `beginner_chord_concept_router_escape`.
- Added exploratory smoke built-in prompts:
  - `What's a G chord even mean?`
  - `What does a C chord mean?`
  - `What notes are in a D chord?`
  - `Where is a G chord?`
  - `How do I play G on E9?`
  - `What makes an E minor chord minor?`
  - `What is the vi chord in G?`
- Added question-bank rows `C045` through `C051` with `expected_contract: copedent_fretboard`.
- Added unit coverage proving:
  - Bad beginner chord concept answers with fragments/sources/no fretboard fail.
  - Clean beginner major concept answers with tones, interval explanation, E9 positions, source-free response, and fretboard payload pass.
  - Clean beginner minor concept answers with flat-third explanation, practical E9 application, source-free response, and fretboard payload pass.

## Exploratory Smoke
- Command used:

```bash
.venv/bin/python scripts/run_exploratory_answer_smoke.py \
  --base-url http://127.0.0.1:8783 \
  --output /tmp/steel_guitar_rag-beginner-chord-concept-smoke.md \
  --json-output /tmp/steel_guitar_rag-beginner-chord-concept-smoke.json
```

- Output artifacts:
  - `/tmp/steel_guitar_rag-beginner-chord-concept-smoke.md`
  - `/tmp/steel_guitar_rag-beginner-chord-concept-smoke.json`
- Note: outputs were written to `/tmp` to avoid touching `corpus-private` or `corpus-v2`.

## Smoke Totals
- Total prompts: 185
- Pass: 99
- Warn: 80
- Fail: 6

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

## Warning Clusters
- `warn:source_excerpt_unrelated`: 211
- `warn:source_excerpt_too_short`: 37
- `warn:low_teaching_value`: 7

## Tests And Checks
- `git diff --check` - passed.
- `.venv/bin/python -m pytest tests/test_answer_eval.py tests/test_full_answer_quality_eval.py` - passed, `46 passed`.
- `.venv/bin/python -m pytest tests/test_api_search.py tests/test_fretboard_examples.py` - passed, `194 passed`.
- `.venv/bin/python -m pytest` - passed, `531 passed`.
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
  - `docs/handoffs/task-completions/2026-06-13-0026-15-beginner-chord-concept-smoke.md`
- Deleted files:
  - None.
- Generated artifacts:
  - `/tmp/steel_guitar_rag-beginner-chord-concept-smoke.md`
  - `/tmp/steel_guitar_rag-beginner-chord-concept-smoke.json`

## Integration Notes
- This is a real product failure, not an environment/setup issue. The local API was reachable.
- The six failing prompts should route to deterministic, steel-specific beginner chord/theory answers with fretboard payloads and no source cards.
- `What is the vi chord in G?` already passes, so the existing function/minor route is working for that explicit phrasing.
- `integration-status.md` should be refreshed to mark this QA lane as blocked by beginner chord concept routing failures.
- The missing Lane 05 prerequisite handoff should be resolved or superseded by the next backend handoff.

## Risk Assessment
- Risk: Low for this QA change.
- Why: changes are confined to eval/smoke scripts, tests, and fixtures. No runtime answer behavior or data stores were modified.
- Rollback: revert the QA/eval changes and this handoff if Lane 05 needs a different bucket naming or fixture strategy.

## Commit Readiness
- Not ready to commit.

The tests are green, but the live exploratory smoke exposed six hard product failures. Commit should wait for Lane 05 to implement or confirm the beginner chord concept router, then Lane 15 should rerun this smoke.

## Suggested Next Step
- Recommended lane: `05 Backend / RAG Integration`.
- Suggested prompt: implement deterministic routing for vague beginner chord/theory prompts such as `What's a G chord even mean?`, `What does a C chord mean?`, `What notes are in a D chord?`, `Where is a G chord?`, `How do I play G on E9?`, and `What makes an E minor chord minor?`. The response should include beginner chord tones, root/third/fifth or flat-third interval explanation, steel-specific E9 application, top-level fretboard payload with positions, empty sources, no weak-source warning, and no SGF/forum fragments.

## Current Status
- QA coverage has been added and passes locally.
- Exploratory smoke now catches the vague beginner chord/theory failures.
- Product status: blocked until beginner chord concept prompts route deterministically.

## Remaining Blockers
- Six live loopback API prompts still fall through to retrieval/forum fragments without deterministic visual payloads.
- Expected Lane 05 beginner-router handoff was not present.

## Recommended Next Lane
- `05 Backend / RAG Integration` to implement the deterministic beginner chord concept route.
