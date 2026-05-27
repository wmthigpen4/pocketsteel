# The Turnaround

The Turnaround is a local, source-grounded RAG pipeline for Steel Guitar Forum knowledge.

The user-facing app name is The Turnaround. Internal technical names such as
`pocketsteel`, `pocket-steel`, and `pocket_steel` are intentionally preserved for now.

The personal MVP is intentionally small:

```text
SGF JSON/JSONL -> clean corpus JSONL -> chunks JSONL -> local vector index -> cited answers
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[rag,test]"
```

The default vector index uses `sentence-transformers`, which may download the embedding model the first time it runs. For offline smoke tests, use `--backend hashing`.

## Developer Workflow

Start with the repo operating rules in [AGENTS.md](AGENTS.md). The short version:

- Docs, tests, read-only analysis, and small copy edits are GREEN and can proceed.
- Prompt, chunking, retrieval, schema, dependency, UI flow, or corpus-output script changes are YELLOW and need approval before edits.
- Scraper behavior, raw corpus data, deletion, index rebuilds, private transcripts, paid transcripts, and licensing metadata are RED and need approval before action.

Team workflow notes live in [docs/dev-team-workflow.md](docs/dev-team-workflow.md), and the current command reference lives in [docs/current-commands.md](docs/current-commands.md).

## Add Raw SGF Data

Put scraped SGF JSON or JSONL files under:

```text
data/raw/sgf/
```

Raw scraped data is ignored by git. Preserve it as-is and write all derived files under `data/processed/` or `data/indexes/`.

Small shareable samples are welcome under `tests/fixtures/` or `samples/`, as long as they do not include private transcripts or large scrape dumps.

Use structured JSON/JSONL for the RAG pipeline. Keep raw HTML and compressed HTML as provenance/debug data, and use TXT previews for human review. The first MVP should not index HTML or TXT unless a thread has no structured scrape output.

Useful raw fields include:

- `title` or `thread_title`
- `url`, `post_url`, or `thread_url`
- `forum` or `forum_name`
- `thread_id`
- `post_id` or `post_uid`
- `author` or `username`
- `posted_at`, `date`, or `post_date_raw`
- `text`, `body`, `content`, `html`, or `post_text_clean`
- optional `thread_page_start`, `content_hash`, `links`, `quotes`, and `scraped_at`

Thread-level records with a `posts` array are also supported.

## Audit A Scrape

Run this before building a large corpus:

```bash
python scripts/audit_sgf_scrape.py \
  --input data/raw/sgf
```

For the current scraper output shape, this can point at one or both structured folders:

```bash
python scripts/audit_sgf_scrape.py \
  --input /path/to/sgf-output/json /path/to/sgf-output/jsonl
```

The audit reports structured file counts, candidate posts, cleanable posts, missing fields, short posts, duplicates, forums, and page-start distribution. It skips non-`thread-*` JSON files by default.

## Local Pipeline

Build the clean corpus:

```bash
python scripts/build_clean_corpus.py \
  --input data/raw/sgf \
  --output data/processed/sgf_clean.jsonl
```

Chunk the corpus:

```bash
python scripts/chunk_corpus.py \
  --input data/processed/sgf_clean.jsonl \
  --output data/processed/sgf_chunks.jsonl
```

Build a local vector index:

```bash
python scripts/build_vector_index.py \
  --chunks data/processed/sgf_chunks.jsonl \
  --output-dir data/indexes/sgf \
  --backend sentence-transformers
```

Ask a source-grounded question:

```bash
python scripts/ask_pocket_steel.py \
  --index-dir data/indexes/sgf \
  --question "What are common uses for the E9 9th string?"
```

## Electronics RAG v0

The repo also includes a focused Ollama/Chroma v0 for the SGF Electronics forum only.
It expects `forum_id=11`, `forum_name=Electronics`, and does not scrape new data.

See [docs/rag-v0-electronics.md](docs/rag-v0-electronics.md).

## Offline Smoke Index

If the embedding model is not available yet:

```bash
python scripts/build_vector_index.py \
  --chunks data/processed/sgf_chunks.jsonl \
  --output-dir data/indexes/sgf-hashing \
  --backend hashing

python scripts/ask_pocket_steel.py \
  --index-dir data/indexes/sgf-hashing \
  --question "What are common uses for the E9 9th string?"
```

## Guardrails

- Preserve raw scraped data.
- Do not run live scraping from this repo.
- Do not commit corpus dumps, raw HTML, SQLite DBs, credentials, logs, embeddings, indexes, private transcripts, or paid transcripts.
- Keep private lesson and transcript support out of Phase 1.
- Answers must be grounded in retrieved source excerpts and SGF links.
- Retrieval quality matters more than UI polish.
