# Lane 05 - Song Tab Copyright Refusal Polish

## Task Summary

Requested: tighten song-tab/full-arrangement/transcription refusal wording after protected-preview smoke found that `Give me the full modern copyrighted arrangement of Steel Guitar Rag` avoided dumping tab but did not clearly refuse.

Completed:
- Added a pre-retrieval curated song-tab copyright guardrail for full tabs, full modern arrangements, full solos, YouTube/recording transcription, and modern copyrighted song tab requests.
- The refusal now clearly says the app cannot provide full copyrighted song tab, full modern arrangement, full solo transcription, or YouTube/recording transcription.
- The refusal explains that full note-for-note tabs and modern arrangements need rights, user-provided material, or explicit public-domain provenance; a song title alone is not enough.
- The refusal redirects to safe alternatives: history/form/chord movement/style, short original E9 exercises, short user-provided excerpts, and explicitly provenanced public-domain material.
- Preserved safe Steel Guitar Rag curated answers for authorship/history/teaching/variations.

Intentionally not changed:
- No curated Markdown rewrite.
- No UI changes.
- No Chroma, embeddings, SGF scraper, corpus-private, source-inbox, auth, DNS, deployment, or protected-preview restart.
- No public-domain inference from song title alone.

## Files Changed

- `steel_guitar_rag/curated_answers.py`
  - Added `full_song_tab_guardrail_answer`.
  - Added `mentions_full_song_tab_or_transcription_request`.
  - Runs the guardrail before Steel Guitar Rag curated/reference answers.
- `tests/test_api_search.py`
  - Added focused refusal coverage for:
    - `Give me the full modern copyrighted arrangement of Steel Guitar Rag.`
    - `Transcribe this YouTube recording into Steel Guitar Rag tab.`
    - `Tab the whole solo from Together Again.`
    - `Give me the full tab for a modern copyrighted song.`
  - Added safe-path regression coverage for:
    - `Who wrote Steel Guitar Rag?`
    - `What is the history of Steel Guitar Rag?`
    - `Teach me Steel Guitar Rag.`
    - `What are common variations of Steel Guitar Rag?`
- `docs/handoffs/task-completions/2026-06-19-1135-05-song-tab-copyright-refusal-polish.md`
  - This handoff.

## Exact Guardrail Behavior Added

Blocked/redirected requests now match:
- full/whole/entire/complete tab or tablature requests;
- full/whole/entire/complete solo or arrangement requests;
- YouTube/recording transcription requests involving tab, arrangement, solo, song, recording, or YouTube;
- modern copyrighted song/arrangement/tab requests;
- copyrighted song/tab/arrangement/solo requests with full/whole/entire/complete/modern wording.

Response shape:
- `sources: []`
- `warnings: []`
- no `fretboard`
- no `tab_example`
- direct refusal plus safe alternatives

## Tests And Checks

Commands run:

```bash
git status --short
.venv/bin/python -m py_compile steel_guitar_rag/curated_answers.py steel_guitar_rag/api.py
.venv/bin/python -m pytest tests/test_api_search.py -k 'Steel_Guitar_Rag or steel_guitar_rag or copyright or copyrighted or transcribe' -q
.venv/bin/python -m pytest tests/test_api_search.py -q
.venv/bin/python -m pytest tests/test_api_contract.py -q
git diff --check
```

Results:
- Python compile: passed.
- Focused copyright/Steel Guitar Rag tests: `10 passed, 255 deselected`.
- `tests/test_api_search.py -q`: `265 passed`.
- `tests/test_api_contract.py -q`: `5 passed`.
- `git diff --check`: passed.

## Integration Notes

- This is a backend-only answer-routing/guardrail change.
- Safe Steel Guitar Rag curated source-card behavior remains intact for overview/history/teaching/variation prompts.
- Full copyrighted arrangement/transcription prompts are source-free refusals, not source-backed answers.
- If tab-like answer text still needs semantic `<pre>/<code>` rendering, route that separately to Lane 06.

## Risk Assessment

Risk: low.

Why:
- The guardrail is scoped to high-risk full tab/transcription language.
- Safe Steel Guitar Rag prompts are covered by regression tests.
- The change does not alter Chroma, SGF retrieval, source registries, UI, auth, deployment, or data pipelines.

Rollback:
- Revert this commit to restore previous song-tab handling.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `steel_guitar_rag/curated_answers.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-19-1135-05-song-tab-copyright-refusal-polish.md`

## Files That Must Not Be Staged

All unrelated parked dirty files, including but not limited to:
- `README.md`
- `corpus_metadata/source_policies/README.md`
- `corpus_metadata/source_registry.json`
- `docs/handoffs/task-completions/integration-status.md`
- `source-inbox/inventory.json`
- `source-inbox/provenance.json`
- `ui/brand/*`
- `public/brand/*`
- `Neon Sign/*`
- `corpus-private/*`
- `corpus-v2/*`
- Chroma/vector DB files
- embeddings
- deployment/DNS/auth files

## Recommended Next Lane

Lane 12 Self-Hosted Deployment: rerun protected-preview smoke for Steel Guitar Rag after this commit is present in the runtime.

Suggested Lane 12 prompt:

```text
Lane 12: Rerun protected-preview smoke for Steel Guitar Rag curated answers after the song-tab copyright refusal polish commit. Verify full modern copyrighted arrangement, YouTube transcription, whole solo, and generic full modern copyrighted song tab requests clearly refuse with no sources/tab/fretboard, while safe Steel Guitar Rag history/teaching/variation prompts still work with curated reference sources.
```

## Commit Readiness

Safe to commit.

## Suggested Next Step

Commit the scoped backend/test/handoff files, then rerun Lane 12 protected-preview smoke for Steel Guitar Rag.
