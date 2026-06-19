# Lane 05 - Steel Guitar Rag Curated Reference

## Task Summary

Requested: add the attached curated `steel-guitar-rag-expert-reference.md` Markdown file into the app's knowledge resources, wire it so song-specific Steel Guitar Rag questions prefer it, preserve citations/links/headings/tab formatting, add tests, and commit if checks pass.

Completed:
- Copied the Markdown into the runtime curated resource area. Citations, links, headings, and tab/code-block formatting were preserved; two trailing spaces in the metadata header were removed so `git diff --check` passes.
- Added a small curated song-reference loader for Steel Guitar Rag.
- Replaced the older hardcoded Steel Guitar Rag answer branch with resource-backed answers.
- Attached curated source cards for the local reference plus UCSB DAHR, Guy Cundell, SecondHandSongs, and Easy Song source links.
- Added API tests for history/authorship, tab formatting, variations, source metadata, and resource checksum.

Intentionally not changed:
- No Chroma/vector DB work.
- No embeddings regenerated.
- No SGF scraper or corpus ingestion changes.
- No global curated source registry edits because `corpus_metadata/source_registry.json` was already dirty with unrelated work.
- No UI, auth, deployment, DNS, source-inbox, or private corpus changes.

## Files Changed

- `pocketsteel/resources/curated/steel-guitar-rag-expert-reference.md`
  - New runtime curated Markdown resource copied from the attached source.
  - Only change from the attachment: removed two trailing spaces in the metadata header for `git diff --check`.
  - SHA-256: `996b7b8cbf12ff09592726421d6ea4cf7cbd072ebd531d230bbd30b6bbf83c8a`
- `pocketsteel/curated_song_references.py`
  - New loader/source-card/answer helper for the Steel Guitar Rag curated reference.
- `pocketsteel/curated_answers.py`
  - Added optional `CuratedAnswer.source_cards`.
  - Routed Steel Guitar Rag questions through the curated reference helper.
- `pocketsteel/api.py`
  - Allows curated answers to supply curated source cards in both pre-retrieval and normal curated-answer branches.
- `tests/test_api_search.py`
  - Removed Steel Guitar Rag from the source-free SGF quarantine test.
  - Added dedicated source-backed tests for Steel Guitar Rag resource discoverability and tab formatting.
- `docs/handoffs/task-completions/2026-06-19-1053-05-steel-guitar-rag-curated-reference.md`
  - This handoff.

## Tests And Checks

Commands run:

```bash
.venv/bin/python -m pytest tests/test_api_search.py -k 'Steel_Guitar_Rag or steel_guitar_rag' -q
.venv/bin/python -m py_compile pocketsteel/curated_song_references.py pocketsteel/curated_answers.py pocketsteel/api.py
git diff --check
.venv/bin/python -m pytest tests/test_api_search.py -q
.venv/bin/python -m pytest tests/test_api_contract.py -q
.venv/bin/python -m pytest
git status --short
```

Results:
- Resource checksum verification: passed.
- Focused Steel Guitar Rag tests: `4 passed, 259 deselected`.
- Python compile checks: passed.
- `tests/test_api_search.py -q`: `263 passed`.
- `tests/test_api_contract.py -q`: `5 passed`.
- Full pytest: `766 passed`.
- `git diff --check`: passed.

## Retrieval / Indexing Notes

This is a curated resource path, not Chroma retrieval:
- The Markdown lives at `pocketsteel/resources/curated/steel-guitar-rag-expert-reference.md`.
- `pocketsteel/curated_song_references.py` loads the Markdown directly.
- Steel Guitar Rag questions are recognized by the existing curated answer route.
- The answer payload includes curated `sources` cards with `source_system: curated_reference`.
- The tab answer extracts the original teaching-study code block from the Markdown and returns it with the original code-fence formatting.

Covered prompts:
- `What is Steel Guitar Rag?`
- `Who wrote Steel Guitar Rag?`
- `Show me Steel Guitar Rag tab`
- `What are common variations of Steel Guitar Rag?`

## Risk Assessment

Risk: low.

Reasoning:
- The change is narrowly scoped to one curated song resource.
- No retrieval ranking, embeddings, Chroma, scraping, auth, deployment, or UI paths changed.
- Source-card support is additive through a default-empty `CuratedAnswer.source_cards` field.

Rollback:
- Revert the commit to restore the previous hardcoded Steel Guitar Rag answers and remove the runtime resource.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `pocketsteel/resources/curated/steel-guitar-rag-expert-reference.md`
- `pocketsteel/curated_song_references.py`
- `pocketsteel/curated_answers.py`
- `pocketsteel/api.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-19-1053-05-steel-guitar-rag-curated-reference.md`

## Files That Must Not Be Staged

All unrelated parked dirty files, including but not limited to:
- `README.md`
- `corpus_metadata/source_policies/README.md`
- `corpus_metadata/source_registry.json`
- `deploy/landing/index.html`
- `docs/handoffs/task-completions/integration-status.md`
- `source-inbox/inventory.json`
- `source-inbox/provenance.json`
- `ui/brand/*`
- `ui/steel-guitar-rag-landing.html`
- `public/brand/*`
- `corpus-private/*`
- `corpus-v2/*`
- `Chroma/vector DB files`
- `Neon Sign/*`

## Recommended Next Lane

Lane 15 QA / Answer Eval can run a small song-specific smoke:
- `What is Steel Guitar Rag?`
- `Who wrote Steel Guitar Rag?`
- `Show me Steel Guitar Rag tab`
- `Teach me Steel Guitar Rag`
- `What are common variations of Steel Guitar Rag?`

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 15 prompt:

```text
Lane 15: QA the Steel Guitar Rag curated reference slice. Verify song-specific answers use curated reference source cards, preserve the original teaching-study tab formatting, avoid full copyrighted tab, and do not regress SGF quarantine/source-card behavior.
```
