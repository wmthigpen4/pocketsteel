# 2026-06-19 11:51 - Lane 05 - Blocked Song Tab Routing Fix

## Task Summary

Fixed the protected-preview blocker where blocked full-song-tab / transcription prompts could route through the Steel Guitar Rag curated reference path and display source cards or educational tab-like content.

Completed:

- Added an API-level pre-retrieval guard for full copyrighted song tab, full modern arrangement, full solo transcription, and YouTube/recording transcription requests.
- Ensured this guard returns before Steel Guitar Rag curated routing, retrieval, source-card assembly, fretboard attachment, or tab-example attachment.
- Strengthened API tests so blocked prompts are covered in both normal `ask` mode and `tab` mode.

Intentionally not changed:

- No UI files.
- No curated Markdown rewrite.
- No scraping, embeddings, Chroma, auth, DNS, deployment, or corpus-private work.
- No public-domain inference from song title.

## Files Changed

- `pocketsteel/api.py`
  - Imported `full_song_tab_guardrail_answer`.
  - Added an early `/api/answer` return path immediately after request parsing/classification.
  - The guarded response has `sources: []`, `warnings: []`, no `fretboard`, and no `tab_example`.
- `tests/test_api_search.py`
  - Expanded full-song-tab/transcription regression coverage to assert both `ask` and `tab` mode behavior.
  - Added assertions that educational Steel Guitar Rag tab/variations text is not included in blocked responses.
- `docs/handoffs/task-completions/2026-06-19-1151-05-blocked-song-tab-routing-fix.md`
  - This handoff.

## Routing Order Fixed

New `/api/answer` order for these blocked prompts:

1. Parse/authenticate request.
2. Classify answer intent.
3. Run `full_song_tab_guardrail_answer(question)`.
4. If matched, return the clean refusal payload immediately.
5. Do not call Steel Guitar Rag curated answer routing, retrieval/search, source-card selection, fretboard generation, or tab-example attachment.

This makes the copyright/transcription guardrail win before the Steel Guitar Rag `tab`, `teach`, `variations`, or source-card routes.

## Blocked Response Payload Behavior

Exact prompts covered:

- `Give me the full modern copyrighted arrangement of Steel Guitar Rag.`
- `Transcribe this YouTube recording into Steel Guitar Rag tab.`
- `Tab the whole solo from Together Again.`
- Existing generic regression: `Give me the full tab for a modern copyrighted song.`

Expected/verified payload:

- Clear refusal/redirect text starts with `I can’t provide a full copyrighted song tab`.
- Explains full song tabs / modern arrangements require rights, user-provided material, or explicit public-domain provenance.
- Offers safe alternatives: history/form/style, short original E9 exercise, short user-provided excerpt, or explicit public-domain material.
- `sources == []`.
- `warnings == []`.
- No `fretboard`.
- No `tab_example`.
- No code block / educational tab-like Steel Guitar Rag study.
- No variations-style answer text.

Safe curated Steel Guitar Rag prompts remain covered by existing tests:

- `Who wrote Steel Guitar Rag?`
- `What is the history of Steel Guitar Rag?`
- `Teach me Steel Guitar Rag.`
- `What are common variations of Steel Guitar Rag?`

## Tests And Checks

Run from `/Users/cory/Documents/Pocket Steel`:

- `git status --short`
  - Large unrelated dirty/untracked worktree already present; scoped files are `pocketsteel/api.py`, `tests/test_api_search.py`, and this handoff.
- `.venv/bin/python -m py_compile pocketsteel/curated_answers.py pocketsteel/api.py`
  - Passed.
- `.venv/bin/python -m pytest tests/test_api_search.py -k 'Steel_Guitar_Rag or steel_guitar_rag or copyright or copyrighted or transcribe or Together_Again' -q`
  - Passed: `10 passed, 255 deselected`.
- `.venv/bin/python -m pytest tests/test_api_search.py -q`
  - Passed: `265 passed`.
- `.venv/bin/python -m pytest tests/test_api_contract.py -q`
  - Passed: `5 passed`.
- `git diff --check`
  - Passed.

## Integration Notes

- Current starting HEAD: `b2190c9`.
- This is a backend-only fix.
- Lane 12 should rerun protected-preview smoke at the new commit because the observed failure was protected-preview behavior.
- Lane 06 tab/code rendering remains separate and was not touched.

## Risk Assessment

Risk: Low.

Reason:

- The new branch is narrowly scoped to already-recognized blocked song-tab/transcription requests.
- Safe Steel Guitar Rag curated answers continue through the existing route.
- The response schema is unchanged.

Rollback:

- Revert the `pocketsteel/api.py` early guard and the associated test update.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `pocketsteel/api.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-19-1151-05-blocked-song-tab-routing-fix.md`

## Files That Must Not Be Staged

- Existing unrelated dirty files, including but not limited to:
  - `README.md`
  - `corpus_metadata/source_policies/README.md`
  - `corpus_metadata/source_registry.json`
  - `docs/handoffs/task-completions/integration-status.md`
  - `rag_answer.py`
  - `rag_build_clean_corpus.py`
  - `rag_chunk_corpus.py`
  - `rag_embed_chroma.py`
  - `source-inbox/inventory.json`
  - `source-inbox/provenance.json`
  - `ui/brand/*`
  - `public/brand/*`
  - `Neon Sign/`
  - Any corpus-private, Chroma/vector, deployment, auth, source-inbox raw/provenance, generated report, or design-asset files.

## Recommended Next Lane

Lane 12 protected-preview smoke.

Suggested prompt:

`Lane 12: Rerun protected-preview smoke for Steel Guitar Rag copyright/tab refusal using the new backend commit. Verify blocked prompts return no sources, no warnings, no fretboard, and no tab_example, and verify safe Steel Guitar Rag history/teaching/variation prompts still show curated source cards.`

## Commit Readiness

Safe to commit.
