# Electronics RAG Data

This directory holds generated artifacts for Steel Guitar RAG RAG v0, built only from Steel Guitar Forum Electronics posts.

Generated files:

- `clean_corpus.jsonl`: cleaned post-level corpus with SGF metadata preserved.
- `clean_corpus_report.json`: source row counts and skip reasons.
- `chunks.jsonl`: retrieval chunks that preserve thread boundaries and include `source_url` and `thread_title`.
- `chunk_report.json`: chunk counts and token statistics.
- `chroma/`: local Chroma vector store built with Ollama embeddings.

Rebuild from the project root:

```bash
python3 -m pip install -r requirements-rag.txt
python3 rag_build_clean_corpus.py
python3 rag_chunk_corpus.py
EMBEDDING_MODEL=bge-m3 python3 rag_embed_chroma.py --reset
```

Pass `--input-glob` to `rag_build_clean_corpus.py` if `sgf-output/` is stored in a separate scraper checkout.

This data set intentionally excludes Tablature and paid/private lesson transcripts.
