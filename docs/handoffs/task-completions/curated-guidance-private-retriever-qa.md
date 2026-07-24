# Curated Guidance Private Retriever QA

## Task Summary

Requested: QA review the isolated private-review `curated_guidance` retriever slice implemented behind `ENABLE_CURATED_GUIDANCE_RETRIEVAL`.

Completed:
- Reviewed `steel_guitar_rag/curated_guidance_retriever.py` for isolation, feature-flag behavior, private file handling, returned metadata, excerpt limits, and quality filtering.
- Reviewed `tests/test_curated_guidance_retriever.py` for meaningful coverage.
- Rechecked the ingestion/eval support scripts and prior curated-guidance handoffs.
- Ran focused retriever tests, compile checks, offline retrieval eval, flag-enabled local smoke, `git diff --check`, `git status --short`, and `git check-ignore`.

Intentionally not changed:
- No `/api/answer` wiring.
- No production UI changes.
- No SGF retrieval changes.
- No Chroma/vector store writes.
- No embeddings.
- No scraping.
- No auth, DNS, deployment, or public route changes.
- No staging or commit.

## Pass/Fail Decision

Pass. QA approves this slice for Repo Steward exact-path staging.

No blocking bugs found.

One integration caution:
- `search_curated_guidance(...)` defaults to the approved private JSONL path, but accepts an `input_path` parameter as a test seam. That is acceptable for this isolated slice, but future production/API callers should not expose a user- or request-controlled path.

## Files Reviewed

- `steel_guitar_rag/curated_guidance_retriever.py`
- `tests/test_curated_guidance_retriever.py`
- `scripts/ingest/build_curated_guidance_corpus.py`
- `scripts/ingest/validate_curated_guidance_corpus.py`
- `scripts/eval/eval_curated_guidance_retrieval.py`
- `docs/handoffs/task-completions/curated-guidance-inventory.md`
- `docs/handoffs/task-completions/curated-guidance-ingestion-spike.md`
- `docs/handoffs/task-completions/curated-guidance-qa-retrieval-eval.md`
- `docs/handoffs/task-completions/curated-guidance-private-retriever-plan.md`

## Safety And Privacy Findings

Feature flag:
- Correct. `ENABLE_CURATED_GUIDANCE_RETRIEVAL` defaults off.
- Enabled values are `1`, `true`, `yes`, and `on`.
- When disabled, `search_curated_guidance(...)` returns `[]` before checking file existence or loading JSONL.

Private file handling:
- Correct for this slice. Default input path is `corpus-private/curated-guidance/normalized/curated-guidance-documents.jsonl`.
- The module does not load private JSONL unless the feature flag is enabled.
- The module is not imported by `/api/answer`, SGF retrieval, Chroma search, UI, auth, deployment, or scraper paths.
- `read_jsonl(...)` validates that rows have `content_layer=curated_guidance`.
- `row_is_retrievable(...)` requires `content_layer=curated_guidance`, `visibility=private_review`, and `needs_review is True`.

Returned data:
- Full private `body` text is not returned in `CuratedGuidanceResult.as_dict()`.
- Returned fields are limited to:
  - `title`
  - `source_filename`
  - `source_path`
  - `content_layer`
  - `visibility`
  - `score`
  - `quality_flags`
  - `excerpt`
- The retriever does not print or log private body text.

Excerpt limits:
- Correct. `EXCERPT_LIMIT=500`.
- Unit tests assert `len(excerpt) <= 500`.
- Flag-enabled smoke over the real ignored JSONL returned three results per query with 500-character excerpts.

Quality filtering:
- Correct for the documented spike behavior.
- Excluded flags:
  - `body_under_100_words`
  - `missing_topic_tags`
  - `no_steel_specific_terms`
  - `possible_transcript_residue`
- Demoted flags:
  - `body_over_reasonable_chunk_size`
  - `broad_combined_card`
  - `contains_player_should_phrase`
  - `first_person_instructor_phrasing`
  - `possible_duplicate_files_by_hash`
- Duplicate hashes are detected at search time and annotated with `possible_duplicate_files_by_hash`.
- Broad cleanup/spec rows are detected by title/path and demoted.

Isolation:
- Confirmed via `rg`: `curated_guidance` references are limited to the new retriever, its tests, ingest/eval scripts, and handoffs.
- No SGF retrieval, Chroma, API answer routing, UI, auth, DNS, deployment, or scraper files are wired to this retriever.

## Test Coverage Review

`tests/test_curated_guidance_retriever.py` covers:
- Feature flag defaults off and enabled values.
- Disabled flag returns no results even when JSONL exists.
- Enabled flag loads local private-review JSONL.
- Returned metadata includes `content_layer=curated_guidance` and `visibility=private_review`.
- Excerpt length is capped.
- Bad rows are excluded for short body / missing topic metadata.
- Duplicate rows are demoted and annotated.
- Teaching queries retrieve expected top results.
- Non-teaching/off-domain query does not search curated guidance.

Coverage is meaningful for this isolated slice.

Suggested future test if this gets wired into production:
- Assert no `/api/answer` response includes curated guidance unless auth/private-review gates explicitly allow it.
- Assert the optional `input_path` parameter is not exposed to request/user input.

## Checks Run

```bash
git status --short
git diff --name-only
rg -n "curated_guidance|ENABLE_CURATED_GUIDANCE|search_curated_guidance|CuratedGuidance" steel_guitar_rag tests scripts docs/handoffs/task-completions/curated-guidance-private-retriever-plan.md
.venv/bin/python -m pytest tests/test_curated_guidance_retriever.py -q
.venv/bin/python -m py_compile steel_guitar_rag/curated_guidance_retriever.py tests/test_curated_guidance_retriever.py scripts/ingest/build_curated_guidance_corpus.py scripts/ingest/validate_curated_guidance_corpus.py scripts/eval/eval_curated_guidance_retrieval.py
.venv/bin/python scripts/eval/eval_curated_guidance_retrieval.py
ENABLE_CURATED_GUIDANCE_RETRIEVAL=1 .venv/bin/python - <<'PY'
from steel_guitar_rag.curated_guidance_retriever import search_curated_guidance
queries = [
    "How do I tune a split on string 6?",
    "What is pick blocking?",
    "What are B+C pedals used for?",
    "Can I play the lick without a B-to-Bb lever?",
    "How do I play a harmonized scale over a dominant chord?",
]
for query in queries:
    results = search_curated_guidance(query, top_k=3)
    print(query, len(results), [len(str(r.get("excerpt", ""))) for r in results], [r.get("content_layer") for r in results], [r.get("visibility") for r in results])
PY
git diff --check
git check-ignore -v corpus-private/curated-guidance/normalized/curated-guidance-documents.jsonl corpus-private/reports/curated-guidance-retrieval-eval.md corpus-private/reports/curated-guidance-retrieval-eval.json
```

Results:
- Focused retriever tests: `6 passed in 0.01s`.
- `py_compile`: passed.
- Offline eval: evaluated 10 curated guidance query fixtures; searched 899 rows; wrote ignored reports under `corpus-private/reports/`.
- Flag-enabled local smoke: all 5 teaching queries returned 3 `curated_guidance/private_review` results; returned excerpt lengths were capped at 500.
- `git diff --check`: passed.
- `git check-ignore`: confirmed requested `corpus-private/` outputs are ignored by `.gitignore:103:corpus-private/`.

## Bugs Found

No blocking bugs.

Non-blocking integration caution:
- Keep `input_path` as an internal/test-only seam. Do not expose it through `/api/answer`, UI, or user-controlled config in a future integration slice.

## Corpus-Private Ignore Verification

Confirmed ignored:
- `corpus-private/curated-guidance/normalized/curated-guidance-documents.jsonl`
- `corpus-private/reports/curated-guidance-retrieval-eval.md`
- `corpus-private/reports/curated-guidance-retrieval-eval.json`

Previously reviewed ignored outputs also remain under the ignored `corpus-private/` tree:
- `corpus-private/reports/curated-guidance-inventory-full.md`
- `corpus-private/reports/curated-guidance-validation.md`
- `corpus-private/reports/curated-guidance-validation.json`

## Safe-To-Stage Exact File List

Safe for Repo Steward exact-path staging:
- `steel_guitar_rag/curated_guidance_retriever.py`
- `tests/test_curated_guidance_retriever.py`
- `scripts/ingest/build_curated_guidance_corpus.py`
- `scripts/ingest/validate_curated_guidance_corpus.py`
- `scripts/eval/eval_curated_guidance_retrieval.py`
- `docs/handoffs/task-completions/curated-guidance-inventory.md`
- `docs/handoffs/task-completions/curated-guidance-ingestion-spike.md`
- `docs/handoffs/task-completions/curated-guidance-qa-retrieval-eval.md`
- `docs/handoffs/task-completions/curated-guidance-private-retriever-plan.md`
- `docs/handoffs/task-completions/curated-guidance-private-retriever-qa.md`

If Repo Steward wants to split commits, a clean split is:
- Ingestion/eval spike:
  - `scripts/ingest/build_curated_guidance_corpus.py`
  - `scripts/ingest/validate_curated_guidance_corpus.py`
  - `scripts/eval/eval_curated_guidance_retrieval.py`
  - `docs/handoffs/task-completions/curated-guidance-inventory.md`
  - `docs/handoffs/task-completions/curated-guidance-ingestion-spike.md`
  - `docs/handoffs/task-completions/curated-guidance-qa-retrieval-eval.md`
- Private retriever:
  - `steel_guitar_rag/curated_guidance_retriever.py`
  - `tests/test_curated_guidance_retriever.py`
  - `docs/handoffs/task-completions/curated-guidance-private-retriever-plan.md`
  - `docs/handoffs/task-completions/curated-guidance-private-retriever-qa.md`

## Files That Must Not Be Staged

Private/generated outputs:
- `corpus-private/curated-guidance/normalized/curated-guidance-documents.jsonl`
- `corpus-private/reports/curated-guidance-inventory-full.md`
- `corpus-private/reports/curated-guidance-validation.md`
- `corpus-private/reports/curated-guidance-validation.json`
- `corpus-private/reports/curated-guidance-retrieval-eval.md`
- `corpus-private/reports/curated-guidance-retrieval-eval.json`

Also keep parked/unrelated files unstaged:
- Chroma/vector stores
- embeddings
- raw guidance markdown bodies
- source-inbox raw/provenance files
- corpus-private/corpus-v2 generated outputs
- deployment/DNS/auth/secrets
- UI/public/design assets
- unrelated dirty docs/scripts already present in the worktree

## Risk Assessment

Risk: low for committing this isolated retriever slice.

Why:
- Disabled by default.
- Not wired into production answer routing.
- Reads only local ignored private-review JSONL by default.
- Returns capped excerpts, not full bodies.
- Does not touch SGF retrieval, Chroma, embeddings, scraping, UI, auth, DNS, or deployment.

Residual risk:
- Future integration must preserve auth/private-review gating and must not expose the `input_path` test seam.

Rollback:
- Remove `steel_guitar_rag/curated_guidance_retriever.py`, `tests/test_curated_guidance_retriever.py`, and this QA handoff.
- Leave ignored `corpus-private/` outputs uncommitted.

## Commit Readiness

Safe to commit.

Exact-path staging only. Do not use `git add .`.

## Recommended Next Step

Recommended lane: 01 Repo Steward.

Exact next prompt:

```text
Lane 01 Repo Steward: commit the curated_guidance ingestion/eval and private retriever slices using exact-path staging only. Read `docs/handoffs/task-completions/curated-guidance-qa-retrieval-eval.md` and `docs/handoffs/task-completions/curated-guidance-private-retriever-qa.md`. Stage only the safe-to-stage files listed there. Do not stage `corpus-private/`, guidance markdown bodies, Chroma/vector data, embeddings, source-inbox, deployment/auth/DNS files, UI/design assets, or unrelated parked files. Run `git diff --cached --check`, focused retriever tests, py_compile, and commit if green.
```
