# Curated Guidance Private Retriever Commit

## Task Summary

Requested: exact-path stage and commit only the approved `curated_guidance` ingestion, QA, and private retriever files after Lane 15 QA passed the private retriever review.

Completed:

- Read the curated guidance private retriever QA handoff.
- Confirmed the QA handoff approved exact-path staging for the requested files.
- Ran the QA handoff's focused checks.
- Staged only the ten QA-approved files.
- Committed the scoped slice.

Intentionally not changed:

- No `corpus-private/` generated outputs were staged.
- No generated JSONL or private reports were staged.
- No Chroma/vector store, embedding, source-inbox, deployment, DNS, auth, UI, design, or unrelated dirty files were staged.
- No `/api/answer` wiring was added.
- No production retrieval behavior changed; the retriever remains feature-flagged and isolated.

## Commit

- Commit: `f959769 curated guidance private retriever`

## Files Committed

- `scripts/ingest/build_curated_guidance_corpus.py`
- `scripts/ingest/validate_curated_guidance_corpus.py`
- `scripts/eval/eval_curated_guidance_retrieval.py`
- `steel_guitar_rag/curated_guidance_retriever.py`
- `tests/test_curated_guidance_retriever.py`
- `docs/handoffs/task-completions/curated-guidance-inventory.md`
- `docs/handoffs/task-completions/curated-guidance-ingestion-spike.md`
- `docs/handoffs/task-completions/curated-guidance-qa-retrieval-eval.md`
- `docs/handoffs/task-completions/curated-guidance-private-retriever-plan.md`
- `docs/handoffs/task-completions/curated-guidance-private-retriever-qa.md`

## Files Left Unstaged

Private/generated outputs remain unstaged and ignored:

- `corpus-private/curated-guidance/normalized/curated-guidance-documents.jsonl`
- `corpus-private/reports/curated-guidance-retrieval-eval.md`
- `corpus-private/reports/curated-guidance-retrieval-eval.json`

Broad pre-existing parked work remains unstaged, including:

- corpus/source/provenance docs and metadata;
- source-inbox inventory/provenance files;
- root RAG scripts;
- deploy/static/design files;
- `public/`, `ui/brand/`, `Neon Sign/`;
- historical handoffs and generated assets;
- local cleanup handoffs;
- unrelated tracked dirty files.

## Checks And Tests Run

```bash
git status --short
git diff --check
sed -n '1,260p' docs/handoffs/task-completions/curated-guidance-private-retriever-qa.md
git diff --name-only -- scripts/ingest/build_curated_guidance_corpus.py scripts/ingest/validate_curated_guidance_corpus.py scripts/eval/eval_curated_guidance_retrieval.py steel_guitar_rag/curated_guidance_retriever.py tests/test_curated_guidance_retriever.py docs/handoffs/task-completions/curated-guidance-inventory.md docs/handoffs/task-completions/curated-guidance-ingestion-spike.md docs/handoffs/task-completions/curated-guidance-qa-retrieval-eval.md docs/handoffs/task-completions/curated-guidance-private-retriever-plan.md docs/handoffs/task-completions/curated-guidance-private-retriever-qa.md
.venv/bin/python -m pytest tests/test_curated_guidance_retriever.py -q
.venv/bin/python -m py_compile steel_guitar_rag/curated_guidance_retriever.py tests/test_curated_guidance_retriever.py scripts/ingest/build_curated_guidance_corpus.py scripts/ingest/validate_curated_guidance_corpus.py scripts/eval/eval_curated_guidance_retrieval.py
.venv/bin/python scripts/eval/eval_curated_guidance_retrieval.py
git check-ignore -v corpus-private/curated-guidance/normalized/curated-guidance-documents.jsonl corpus-private/reports/curated-guidance-retrieval-eval.md corpus-private/reports/curated-guidance-retrieval-eval.json
git diff --check
git add -- scripts/ingest/build_curated_guidance_corpus.py scripts/ingest/validate_curated_guidance_corpus.py scripts/eval/eval_curated_guidance_retrieval.py steel_guitar_rag/curated_guidance_retriever.py tests/test_curated_guidance_retriever.py docs/handoffs/task-completions/curated-guidance-inventory.md docs/handoffs/task-completions/curated-guidance-ingestion-spike.md docs/handoffs/task-completions/curated-guidance-qa-retrieval-eval.md docs/handoffs/task-completions/curated-guidance-private-retriever-plan.md docs/handoffs/task-completions/curated-guidance-private-retriever-qa.md
git diff --cached --check
git diff --cached --name-only
git diff --cached --stat
git diff --cached
git commit -m "curated guidance private retriever"
git status --short
git log --oneline -5
```

Results:

- `git diff --check`: passed before staging.
- Focused retriever tests: `6 passed in 0.01s`.
- `py_compile`: passed.
- Offline retrieval eval: evaluated `10` curated guidance query fixtures, searched `899` rows, and wrote ignored private reports under `corpus-private/reports/`.
- `git check-ignore`: confirmed the private JSONL and eval report outputs are ignored by `.gitignore:103:corpus-private/`.
- `git diff --cached --check`: passed.
- Commit succeeded.

## Safety Notes

- The retriever is gated by `ENABLE_CURATED_GUIDANCE_RETRIEVAL` and defaults off.
- The slice is not wired into `/api/answer`, SGF retrieval, Chroma, UI, auth, deployment, or public routes.
- `search_curated_guidance(...)` has an `input_path` test seam. Keep it internal; future production/API callers must not expose user-controlled paths.
- Results return capped excerpts and metadata, not full private guidance bodies.

## Risk Assessment

Risk: low for this isolated commit.

Residual risk:

- Future integration must preserve private-review/auth gating.
- Future integration must avoid blending curated guidance into SGF/forum retrieval without a separate approved plan.
- Private generated artifacts remain ignored and must stay uncommitted.

## Recommended Next Step

Recommended lane: 05 Backend / RAG Integration or 15 QA / Answer Eval, only when explicitly ready for a next slice.

Suggested prompt:

```text
Plan the next curated_guidance integration slice without wiring it into production by default. Read steel_guitar_rag/curated_guidance_retriever.py and the curated guidance handoffs. Preserve ENABLE_CURATED_GUIDANCE_RETRIEVAL default-off behavior, keep private-review gating, do not expose input_path to request/user input, and do not touch corpus-private generated outputs, Chroma/vector stores, embeddings, deployment, auth, DNS, UI, or source-inbox. Stop after a plan unless implementation is explicitly requested.
```

## Commit Readiness

This handoff is uncommitted and should remain parked unless a later docs-only coordination commit explicitly includes it.
