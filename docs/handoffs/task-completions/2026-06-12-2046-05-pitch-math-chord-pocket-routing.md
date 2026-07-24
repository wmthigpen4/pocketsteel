# Pitch-Math Chord/Pocket Routing

## Task Summary
- What was requested: fix fretboard/chord answer generation so plain chord-position, E-lower diagnostic, B9-pocket, and functional V-pocket questions use deterministic pitch math only, with no SGF retrieval fallback.
- What was completed: expanded the E9 pitch-rule layer to emit richer validated position metadata, added deterministic routes for `5-7-8 with E lowered ... B9 pocket` and `Show me V chord pockets in A`, updated the API contract/tests for the richer payload fields, and kept deterministic rule answers source-free.
- What was intentionally not changed: no deployment, DNS, Chroma/vector store, embeddings, scraping, auth, corpus-private data, source-inbox data, or UI rendering changes.

## Files Changed
- Changed files:
  - `steel_guitar_rag/fretboard_examples.py`
  - `steel_guitar_rag/curated_answers.py`
  - `steel_guitar_rag/api_contract.py`
  - `scripts/run_full_answer_quality_eval.py`
  - `tests/fixtures/user_question_bank.json`
  - `tests/test_answer_eval.py`
  - `tests/test_api_contract.py`
  - `tests/test_api_search.py`
  - `tests/test_fretboard_examples.py`
  - `tests/test_export_e9_position_catalog.py` (untracked pre-existing test file; updated for the new generated row count)
- Created files:
  - `docs/handoffs/task-completions/2026-06-12-2046-05-pitch-math-chord-pocket-routing.md`
- Deleted files: none.
- Generated artifacts: temporary curl outputs in `/tmp/answer-g.json`, `/tmp/answer-b.json`, `/tmp/answer-e578.json`, `/tmp/answer-b9.json`, `/tmp/answer-vpockets.json`; not part of repo.

## Tests And Checks
- `python3 -m py_compile steel_guitar_rag/fretboard_examples.py steel_guitar_rag/curated_answers.py steel_guitar_rag/api_contract.py`
  - Result: passed.
- `.venv/bin/python -m pytest tests/test_fretboard_examples.py -q`
  - Initial result: 1 failed due old `positionKind == "starter"` expectation.
  - Final result: 32 passed.
- `.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_api_answer_private_retrieval.py tests/test_answer_eval.py tests/test_full_answer_quality_eval.py`
  - Result: 199 passed.
- `.venv/bin/python -m pytest`
  - Initial result: 1 failed due obsolete `tests/test_export_e9_position_catalog.py` row count.
  - Final result: 489 passed.
- `git diff --check`
  - Result: passed.
- Local curl verification against `127.0.0.1:8783`:
  - `Where all can I play a G chord?`
  - `What does 5-7-8 with E lowered give me at the 3rd fret?`
  - `Is 5-7-8 with E lowered a B9 pocket?`
  - `Show me V chord pockets in A.`
  - `Where all can I play a B chord?`
  - Result: all returned deterministic answers with `sources: []` and `warnings: []`.

## Integration Notes
- Schema/API/component/data contract changes:
  - `FretboardPosition` payload contract now includes scalar/list metadata for:
    - `function`
    - `keyContext`
    - `addedIntervals`
    - `whyUseIt`
  - Existing position payloads still include the previous fields and remain render-safe.
- G payload generated:
  - Count: 44 positions.
  - Visible starter positions: `g-open-3`, `g-af-6`, `g-ab-10`.
  - Includes common open grips at fret 3 in canonical order: `3-4-5`, `4-5-6`, `5-6-8`, `5-7-8`, `6-8-10`.
  - Includes octave equivalents above fret 12, including `g-open-15-octave`, `g-af-18-octave`, `g-ab-22-octave`.
  - Includes validated E-lower full G major grips at frets 8 and 20 for `5-7-8`, `7-8-10`, `4-5-7`, and `1-4-5`.
  - Includes rootless/partial G dominant-color pockets at frets 6 and 18.
- B payload generated:
  - Count: 44 positions.
  - Visible starter positions: `b-open-7`, `b-af-10`, `b-ab-14`.
  - Includes `b-ab-2-lower-octave` as hidden A+B lower-octave alternate.
  - Includes common open grips at fret 7 in canonical order: `3-4-5`, `4-5-6`, `5-6-8`, `5-7-8`, `6-8-10`.
  - Includes validated E-lower full B major grips at frets 0 and 12 for `5-7-8`, `7-8-10`, `4-5-7`, and `1-4-5`.
  - Includes rootless/partial B dominant-color pockets at frets 10 and 22.
- `5-7-8 with E lowered at fret 3` classification:
  - Notes: string 5 = D, string 7 = A, string 8 = F#.
  - Classification: full D major.
  - Additional relationship: against a B root, those notes can sound like rootless B minor 7 color because the B root is omitted.
- `Is 5-7-8 with E lowered a B9 pocket?` answer:
  - Deterministic no/partial answer.
  - It is not a full B9 grip by itself.
  - At frets 0, 12, and 24, the same grip spells B major and omits the b7 and 9 required for full B9.
  - At fret 3, it spells D major and can imply rootless B minor 7 color, not B9.
- `Show me V chord pockets in A` generated:
  - Target: V in A = E.
  - Payload title: `V chord pockets in A (E)`.
  - Count: 19 positions.
  - Visible starter positions: `a-v-e-open-0`, `a-v-e-af-3`, `a-v-e-ab-7`.
  - Includes E-lower full E major pockets at frets 5 and 17.
  - Includes E-lower rootless/partial E dominant-color pockets at frets 3 and 15.
- Assumptions:
  - B9 pocket question without a specified fret should answer conceptually from the confirmed copedent rather than emit a broad visualization payload.
  - `fret 0` is acceptable label wording for the open fret in functional-pocket prose.
  - Rule-derived fretboard answers should keep `sources: []`; deterministic rule metadata remains in `fretboard.sourceContext`.
- Blockers: none.
- Human decisions needed: no.

## Risk Assessment
- Risk: Medium.
- Why: the pitch-engine behavior is deterministic and covered by tests, but it expands the fretboard payload considerably and changes the generated catalog row count from the earlier lane’s expectations.
- Rollback notes: revert changes in `steel_guitar_rag/fretboard_examples.py`, `steel_guitar_rag/curated_answers.py`, the API contract field additions, and the associated tests/fixtures to return to the previous starter-only behavior.

## Commit Readiness
- Safe to commit.

## Suggested Next Step
- Lane 06 UX/UI Design should smoke-test the expanded payload filters in the protected preview.
- Suggested prompt:
  - “Run a protected-preview browser smoke for expanded E9 pitch-engine fretboard payloads. Verify G/B major show starter, alternate, advanced, and dominant filters; verify `5-7-8 with E lowered at the 3rd fret` renders as a focused one-position diagnostic; verify `Show me V chord pockets in A` renders E major and dominant-color pockets without `[object Object]`.”
