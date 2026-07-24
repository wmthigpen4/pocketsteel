## Task summary
- Requested: add invalid chord-symbol validation before retrieval so typo chord questions such as `how. do I play a GF chord?` do not fall through to SGF/forum fragments.
- Completed: added a deterministic chord-symbol guardrail in the fretboard/rules layer for chord-shaped questions.
- Completed: invalid chord tokens now return a source-free clarification before retrieval.
- Completed: valid `G` and `F` chord questions still route to deterministic fretboard-backed answers.
- Completed: `G/F` slash chord questions get a source-free explanation/limitation rather than retrieval fallback.
- Intentionally not changed: no deployment, DNS, Chroma, embeddings, corpus-private, corpus-v2, source-inbox, scraping, provenance/legal files, secrets, `.wrangler`, design assets, auth, or frontend rendering.

## Branch and HEAD
- Branch: `feature/answer-api`
- HEAD: `3bb0ded`

## Root cause
- Root cause bucket: B, chord router missed malformed chord symbols and retrieval took over.
- The deterministic chord parser accepted one-letter roots with optional `#`/`b`; `GF` did not match, so it was not classified as a chord-position/question and fell through to retrieval-shaped answer synthesis.
- The answer layer then made unrelated forum fragments look intentional instead of asking for clarification.

## Route/fallback path before fix
- `how. do I play a GF chord?`
  - did not match deterministic major/minor/function/chord-concept route;
  - did not trigger unsupported chord-quality handling;
  - proceeded to retrieval;
  - source fragments could shape the answer body and source cards.

## Invalid chord validation behavior
- Chord-shaped prompts now extract and validate the chord token for forms like:
  - `how do I play a ___ chord`
  - `where is ___ chord`
  - `what is a ___ chord`
  - `show me ___ chord`
  - `what does ___ chord mean`
- Valid examples are not blocked:
  - `G`
  - `F`
  - `C`
  - `Em`
  - `G7`
  - `B9`
- Slash chord example:
  - `G/F` is recognized as a slash chord and explained as `G over F`; the current visualizer limitation is stated clearly and no fretboard payload is emitted.
- Invalid examples return source-free clarification:
  - `GF`
  - `Cmajorish`
  - `H chord`
  - `Zm`
  - `GmF`
  - random two-letter roots without a slash.

## Before/after
- Prompt: `how. do I play a GF chord?`
- Before: forum-like fragments could appear, with no validation that `GF` is not a standard chord symbol.
- After:
  - `I don’t recognize “GF” as a standard chord name.`
  - suggests `G`, `F`, and `G/F, a G chord over an F bass note`;
  - tells the user to say `G/F` with a slash if that is what they meant;
  - returns `sources: []`, `warnings: []`, and no fretboard payload.

## Valid chord regressions
- `how do I play a G chord?`
  - still returns `G major positions on E9`;
  - includes a top-level fretboard payload;
  - sources remain clean/suppressed for deterministic route.
- `how do I play an F chord?`
  - still returns `F major positions on E9`;
  - visible deterministic positions are `f-open-1`, `f-af-4`, `f-ab-8`;
  - sources remain clean/suppressed for deterministic route.

## Slash chord behavior
- `how do I play a G/F chord?`
  - returns a deterministic clarification:
    `G/F is a slash chord: G over a F bass note.`
  - explains that the current fretboard visualizer does not yet generate separate bass-note/slash-chord diagrams.
  - returns no source cards, no warnings, and no fretboard payload.

## Files changed
- Changed files:
  - `steel_guitar_rag/fretboard_examples.py`
  - `steel_guitar_rag/curated_answers.py`
  - `tests/test_fretboard_examples.py`
  - `tests/test_api_search.py`
- Created files:
  - `docs/handoffs/task-completions/2026-06-13-2352-05-invalid-chord-symbol-guardrail.md`
- Deleted files: none.
- Generated artifacts: none.

## Tests and checks
- `.venv/bin/python -m pytest tests/test_fretboard_examples.py tests/test_api_search.py tests/test_api_contract.py`
  - Result: `210 passed in 0.54s`
- `.venv/bin/python -m pytest tests/test_answer_eval.py tests/test_full_answer_quality_eval.py`
  - Result: `50 passed in 0.22s`
- `git diff --check`
  - Result: passed with no output.
- `.venv/bin/python -m pytest`
  - Result: `551 passed in 4.00s`
- Final `git diff --check`
  - Result: passed with no output.
- Tests skipped: none.

## Integration notes
- Public `/api/answer` shape is unchanged.
- Invalid chord clarification is handled by `visual_fretboard_curated_answer(...)`, so `/api/answer` returns before retrieval with `sources: []`.
- No `response.fretboard` is emitted for invalid symbols or slash-chord limitation answers because no valid correction has been selected.
- The backend still does not emit raw UI geometry.
- Assumption: `G/F` should be treated as recognized-but-not-yet-visualized rather than invalid.
- Blockers: none.
- Human decisions needed: decide whether future slash-chord support should generate a visual payload, and what bass-note semantics the fretboard component should display.

## Risk assessment
- Risk: Low.
- Why: this is a narrow deterministic guardrail for chord-shaped prompts that previously escaped deterministic routing. Valid G/F chord routes are covered by tests.
- Rollback notes: remove the `chord_symbol_guardrail_answer_for_question(...)` call from `visual_fretboard_curated_answer(...)` and remove the helper/tests.

## Commit readiness
- Needs human review first.
- Reason: implementation is test-green, but the worktree contains many unrelated dirty files from other lanes. Do not stage broadly.
- Exact safe-to-stage file list for this task after review:
  - `steel_guitar_rag/fretboard_examples.py`
  - `steel_guitar_rag/curated_answers.py`
  - `tests/test_fretboard_examples.py`
  - `tests/test_api_search.py`
  - `docs/handoffs/task-completions/2026-06-13-2352-05-invalid-chord-symbol-guardrail.md`
- Must remain unstaged unless separately approved:
  - Chroma/vector stores, embeddings, `corpus-private/`, `corpus-v2/`, `source-inbox/`, scraping outputs, provenance/legal dumps, deployment secrets/config, `.wrangler`, DNS config, design assets, and unrelated dirty worktree files.

## Suggested next step
- Lane 15 QA / Answer Eval should rerun beginner/advice smoke including malformed chord-symbol prompts.
- Suggested prompt: `Rerun exploratory smoke for invalid chord-symbol and beginner chord prompts, especially GF, H, G/F, G, and F, and verify no retrieval fragments or source cards appear for deterministic clarification answers.`
