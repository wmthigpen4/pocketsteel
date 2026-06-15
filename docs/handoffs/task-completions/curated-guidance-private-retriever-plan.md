# Curated Guidance Private Retriever Plan

## Task Summary

Lane: 05 Backend / RAG Integration

Requested: plan and implement a separate private-review `curated_guidance` retrieval path behind a feature flag, using the ignored normalized JSONL export from `corpus-private/curated-guidance/normalized/curated-guidance-documents.jsonl`.

Completed:
- Added a standalone local retriever module for private-review curated guidance.
- Added focused unit tests for feature-flag behavior, local JSONL loading, quality filtering, and teaching-query retrieval.
- Verified the existing offline curated-guidance retrieval eval still runs over the ignored 899-row JSONL.
- Verified private generated outputs are ignored by git.

Intentionally not changed:
- No production `/api/answer` routing was changed.
- No protected-preview UI wiring was added.
- No SGF/forum retrieval code was modified.
- No Chroma/vector store, embeddings, scraper, corpus-v2, auth, deployment, DNS, or public rendering code was touched.
- No hosted APIs, external LLMs, or network services are used by the retriever.

## Files Changed

Created:
- `pocketsteel/curated_guidance_retriever.py`
- `tests/test_curated_guidance_retriever.py`
- `docs/handoffs/task-completions/curated-guidance-private-retriever-plan.md`

Read/used from prior lanes:
- `scripts/ingest/build_curated_guidance_corpus.py`
- `scripts/ingest/validate_curated_guidance_corpus.py`
- `scripts/eval/eval_curated_guidance_retrieval.py`
- `docs/handoffs/task-completions/curated-guidance-inventory.md`
- `docs/handoffs/task-completions/curated-guidance-ingestion-spike.md`
- `docs/handoffs/task-completions/curated-guidance-qa-retrieval-eval.md`

Generated/updated ignored artifacts during verification:
- `corpus-private/reports/curated-guidance-retrieval-eval.md`
- `corpus-private/reports/curated-guidance-retrieval-eval.json`

## Retriever Behavior

Module:
- `pocketsteel.curated_guidance_retriever`

Entry points:
- `curated_guidance_retrieval_enabled(env=None) -> bool`
- `search_curated_guidance(query, input_path=..., top_k=5, env=None) -> list[dict]`
- `search_rows(rows, query, top_k=5) -> list[CuratedGuidanceResult]`

Feature flag:
- Env var: `ENABLE_CURATED_GUIDANCE_RETRIEVAL`
- Enabled values: `1`, `true`, `yes`, `on`
- Default: disabled.
- When disabled, `search_curated_guidance(...)` returns `[]` without loading the JSONL.

Input path:
- `corpus-private/curated-guidance/normalized/curated-guidance-documents.jsonl`

Returned metadata:
- `title`
- `source_filename`
- `source_path`
- `content_layer`
- `visibility`
- `score`
- `quality_flags`
- `excerpt`

Privacy behavior:
- Excerpts are capped to 500 characters.
- Full private guidance bodies are never returned.
- The retriever does not print or log private body text.
- Results are limited to `content_layer=curated_guidance` and `visibility=private_review`.

## Filtering Rules

Rows are excluded before scoring when they have:
- `body_under_100_words`
- `missing_topic_tags`
- `no_steel_specific_terms`
- `possible_transcript_residue`

Rows are demoted, not excluded, when they have:
- `body_over_reasonable_chunk_size`
- `broad_combined_card`
- `contains_player_should_phrase`
- `first_person_instructor_phrasing`
- `possible_duplicate_files_by_hash`

Additional local quality checks:
- Duplicate `source_sha256` values are detected at load/search time and marked as `possible_duplicate_files_by_hash`.
- Broad combined-card/spec rows are detected by title/path and demoted.

## Tests And Checks

Commands run:

```bash
.venv/bin/python -m pytest tests/test_curated_guidance_retriever.py -q
```

Result:
- `6 passed in 0.02s`

```bash
.venv/bin/python -m py_compile pocketsteel/curated_guidance_retriever.py scripts/ingest/build_curated_guidance_corpus.py scripts/ingest/validate_curated_guidance_corpus.py scripts/eval/eval_curated_guidance_retrieval.py
```

Result:
- Passed.

```bash
.venv/bin/python scripts/eval/eval_curated_guidance_retrieval.py
```

Result:
- Evaluated 10 curated guidance query fixtures.
- Rows searched: 899.
- Wrote ignored markdown/JSON reports under `corpus-private/reports/`.

```bash
ENABLE_CURATED_GUIDANCE_RETRIEVAL=1 .venv/bin/python - <<'PY'
from pocketsteel.curated_guidance_retriever import search_curated_guidance
queries = [
    "How do I tune a split on string 6?",
    "What is pick blocking?",
    "What are B+C pedals used for?",
    "Can I play the lick without a B-to-Bb lever?",
    "How do I play a harmonized scale over a dominant chord?",
]
for query in queries:
    results = search_curated_guidance(query, top_k=3)
    top = results[0] if results else {}
    print(query, len(results), top.get("score"), top.get("content_layer"), top.get("visibility"), len(str(top.get("excerpt", ""))))
PY
```

Result:
- Each requested teaching query returned 3 `curated_guidance/private_review` results.
- Top excerpt length was 500 characters for each query.

```bash
git diff --check
```

Result:
- Passed.

```bash
git check-ignore -v corpus-private/curated-guidance/normalized/curated-guidance-documents.jsonl corpus-private/reports/curated-guidance-inventory-full.md corpus-private/reports/curated-guidance-validation.md corpus-private/reports/curated-guidance-validation.json corpus-private/reports/curated-guidance-retrieval-eval.md corpus-private/reports/curated-guidance-retrieval-eval.json
```

Result:
- All listed private generated outputs are ignored by `.gitignore:103:corpus-private/`.

## Git Status Notes

Scoped new files from this task:
- `pocketsteel/curated_guidance_retriever.py`
- `tests/test_curated_guidance_retriever.py`
- `docs/handoffs/task-completions/curated-guidance-private-retriever-plan.md`

Prior safe-to-stage files still untracked from earlier curated-guidance lanes:
- `scripts/ingest/build_curated_guidance_corpus.py`
- `scripts/ingest/validate_curated_guidance_corpus.py`
- `scripts/eval/eval_curated_guidance_retrieval.py`
- `docs/handoffs/task-completions/curated-guidance-inventory.md`
- `docs/handoffs/task-completions/curated-guidance-ingestion-spike.md`
- `docs/handoffs/task-completions/curated-guidance-qa-retrieval-eval.md`

The broader worktree contains many unrelated parked changes and untracked files from previous lanes. They were not touched for this slice.

## Safe-To-Stage Files

For a future exact-path Repo Steward commit, the curated-guidance implementation slice can include:
- `pocketsteel/curated_guidance_retriever.py`
- `tests/test_curated_guidance_retriever.py`
- `docs/handoffs/task-completions/curated-guidance-private-retriever-plan.md`

If batching with the already-approved prior curated-guidance ingestion/eval work, include only these additional prior-lane files:
- `scripts/ingest/build_curated_guidance_corpus.py`
- `scripts/ingest/validate_curated_guidance_corpus.py`
- `scripts/eval/eval_curated_guidance_retrieval.py`
- `docs/handoffs/task-completions/curated-guidance-inventory.md`
- `docs/handoffs/task-completions/curated-guidance-ingestion-spike.md`
- `docs/handoffs/task-completions/curated-guidance-qa-retrieval-eval.md`

## Files That Must Remain Uncommitted

Private/generated outputs:
- `corpus-private/curated-guidance/normalized/curated-guidance-documents.jsonl`
- `corpus-private/reports/curated-guidance-inventory-full.md`
- `corpus-private/reports/curated-guidance-validation.md`
- `corpus-private/reports/curated-guidance-validation.json`
- `corpus-private/reports/curated-guidance-retrieval-eval.md`
- `corpus-private/reports/curated-guidance-retrieval-eval.json`

Also do not stage unrelated parked files from other lanes.

## Risks

Risk level: medium-low.

Why:
- The retriever is isolated and disabled by default.
- No production answer routing uses it yet.
- It reads ignored private-review JSONL only when explicitly enabled.
- Ranking is lightweight local scoring; it is suitable for a private-review spike, not final production ranking.

Remaining risks:
- This retriever is not yet integrated with answer composition, source cards, or auth checks.
- The current scoring is deterministic and local but intentionally simple.
- Private-review excerpts are short, but future UI/API wiring must preserve auth and visibility gates.

Rollback:
- Remove `pocketsteel/curated_guidance_retriever.py` and `tests/test_curated_guidance_retriever.py`.
- Leave generated `corpus-private` outputs ignored/uncommitted.
- Since no production routing was changed, rollback has no protected-preview behavior impact.

## Integration Notes

Recommended next lane:
- Lane 15 QA / Answer Eval.

Suggested next prompt:

```text
Lane: 15 QA / Answer Eval
Review the private-review curated_guidance retriever spike. Read `pocketsteel/curated_guidance_retriever.py`, `tests/test_curated_guidance_retriever.py`, and `docs/handoffs/task-completions/curated-guidance-private-retriever-plan.md`. Verify the feature flag defaults off, private-review JSONL loading works only when enabled, quality filters exclude or demote the documented flags, excerpts are capped to 500 characters, and no private generated outputs are staged. Run the focused retriever tests, the offline curated-guidance retrieval eval if the ignored JSONL is present, `git diff --check`, and `git check-ignore` for the corpus-private outputs. Report whether this is ready for Repo Steward exact-path staging.
```

Human decision needed:
- Yes, before wiring curated guidance into `/api/answer`, source cards, protected preview, or production UI.

Commit readiness:
- Safe to commit after QA review, exact-path staging only.
