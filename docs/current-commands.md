# Current Commands

This is the current local command reference for The Turnaround. These commands do not perform live scraping. Commands that rebuild corpus outputs or vector indexes should be treated as YELLOW or RED according to `AGENTS.md`.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[rag,test]"
```

## Safe Checks

```bash
git status --short
git diff --check
pytest
```

Run targeted tests while iterating:

```bash
pytest tests/test_clean_corpus.py
pytest tests/test_chunk_corpus.py
```

## Read-Only Scrape Audit

This audits existing structured scrape output without modifying raw files:

```bash
python3 scripts/audit_sgf_scrape.py --input data/raw/sgf
```

For a separate scraper checkout:

```bash
python3 scripts/audit_sgf_scrape.py --input /path/to/sgf-output/json /path/to/sgf-output/jsonl
```

## Packaged Local Pipeline

These commands write derived corpus or index outputs. Get approval when the task mode requires it.

Build a clean corpus:

```bash
python3 scripts/build_clean_corpus.py \
  --input data/raw/sgf \
  --output data/processed/sgf_clean.jsonl
```

Chunk the clean corpus:

```bash
python3 scripts/chunk_corpus.py \
  --input data/processed/sgf_clean.jsonl \
  --output data/processed/sgf_chunks.jsonl
```

Build a dependency-light smoke index:

```bash
python3 scripts/build_vector_index.py \
  --chunks data/processed/sgf_chunks.jsonl \
  --output-dir data/indexes/sgf-hashing \
  --backend hashing
```

Ask a source-grounded question:

```bash
python3 scripts/ask_pocket_steel.py \
  --index-dir data/indexes/sgf-hashing \
  --question "What are common uses for the E9 9th string?"
```

## Current Forum RAG Scripts

The root-level RAG scripts use existing local forum exports and write to `rag-data/`. They do not scrape. Rebuilding Chroma stores is RED unless explicitly approved.

Build a forum-specific store:

```bash
python3 rag_build_forum.py --slug pedal-steel
```

Build every configured current phpBB forum that is complete in the local manifest:

```bash
python3 rag_build_forum.py --all-complete-current
```

Run stage scripts directly:

```bash
python3 rag_build_clean_corpus.py --forum-id 5 --forum-name "Pedal Steel" --slug pedal-steel
python3 rag_chunk_corpus.py --forum-id 5 --forum-name "Pedal Steel" --slug pedal-steel
python3 rag_embed_chroma.py --forum-id 5 --forum-name "Pedal Steel" --slug pedal-steel --reset
```

Search one forum:

```bash
python3 rag_search.py --slug pedal-steel "What are common uses for the E9 9th string?"
```

Search every built forum store:

```bash
python3 rag_search.py --all-built "What are common uses for the E9 9th string?"
```

Answer from one forum:

```bash
python3 rag_answer.py --slug pedal-steel "What are common uses for the E9 9th string?"
```

Answer from every built forum store:

```bash
python3 rag_answer.py --all-built "What are common uses for the E9 9th string?"
```

## Electronics Eval

Run the lightweight Electronics-only eval:

```bash
python3 eval/run_rag_eval.py
```

Limit questions while smoke testing:

```bash
python3 eval/run_rag_eval.py --limit 3
```

## Legal And Provenance Helpers

Dry-run a source policy snapshot:

```bash
python3 scripts/capture_source_policy_snapshot.py \
  --source-system sgf \
  --policy-url "https://example.com/policy" \
  --policy-text "Policy excerpt here" \
  --dry-run
```

Print the review queue schema without writing:

```bash
python3 scripts/prepare_copyright_review_queue.py --schema
```

Dry-run a small review queue sample:

```bash
python3 scripts/prepare_copyright_review_queue.py \
  --sample-jsonl tests/fixtures/raw_sgf_sample.jsonl \
  --limit 3 \
  --dry-run
```

## Commands Not To Run Without Approval

- Any live scraper command.
- Any command that deletes raw files, generated corpora, SQLite databases, or vector stores.
- `rag_embed_chroma.py --reset` or any other vector index rebuild.
- Broad renames of `pocketsteel`, `pocket-steel`, or `pocket_steel`.
- Commands that mutate private transcripts, paid transcripts, licensing metadata, auth, payments, or access control.
