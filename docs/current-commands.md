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
.venv/bin/python -m pytest
```

Run targeted tests while iterating:

```bash
.venv/bin/python -m pytest tests/test_clean_corpus.py
.venv/bin/python -m pytest tests/test_chunk_corpus.py
```

## Local Answer UI Smoke

Start the same-origin answer UI smoke/dev server:

```bash
PYTHONPATH=. \
STEEL_RAG_CHROMA_PATH="~/Documents/sgf-scrape-test/corpus-unified/vector-stores/chroma" \
STEEL_RAG_CHROMA_COLLECTION="steel_guitar_unified" \
.venv/bin/python scripts/serve_answer_smoke.py --controlled-states --port 8770
```

Start the same-origin answer UI against Cloudflare Access auth config for private-preview verification:

```bash
cd ~/Documents/Pocket\ Steel
source .venv/bin/activate
set -a
source ~/.steel-rag/env/private-preview.env
set +a

PYTHONPATH=. \
.venv/bin/python scripts/serve_answer_smoke.py \
  --host 127.0.0.1 \
  --port 8770 \
  --answer-auth-mode production \
  --auth-provider cloudflare-access
```

Open:

```text
http://127.0.0.1:8770/ui/steel-guitar-rag-mock.html
```

Kill the server before restarting it:

```bash
lsof -tiTCP:8770 -sTCP:LISTEN | xargs kill
```

Run the answer eval against the local server:

```bash
.venv/bin/python scripts/run_answer_eval.py \
  --base-url http://127.0.0.1:8770 \
  --question-bank tests/fixtures/user_question_bank.json \
  --output docs/answer-eval-report.md \
  --json-output /tmp/answer-eval-results.json
```

Restart the server after backend Python changes; the running smoke server does not reload them automatically.

## Frontend And API Tests

Run the frontend/UI checks:

```bash
node --check ui/answer-client.js
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py
.venv/bin/python -m pytest tests/test_public_landing_page.py
```

Run the API and answer contract checks:

```bash
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_answer_eval.py
```

Run the same-origin smoke server checks:

```bash
.venv/bin/python -m pytest tests/test_same_origin_smoke_server.py
```

Run the full test suite:

```bash
.venv/bin/python -m pytest
```

## Phase 3 Corpus-V2 Checks

Run the Phase 3 cleaner, chunker, and preflight tests:

```bash
.venv/bin/python -m pytest \
  tests/test_phase3_clean_classify_chunks.py \
  tests/test_phase3_chunk_v2.py \
  tests/test_phase3_embed_v2_preflight.py
```

Generated `corpus-v2/` data is derived output. Do not commit `corpus-v2/`, Chroma stores, vector files, embedding outputs, or large generated JSONL unless a human explicitly approves the exact generated artifact.

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
