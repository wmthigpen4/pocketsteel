# Pocket Steel RAG v0: Electronics

This v0 RAG pipeline uses only Steel Guitar Forum `forum_id=11`, `forum_name=Electronics`.
It does not scrape anything and does not modify the scraper.

## Inputs

- `sgf-output/jsonl/forum-11/*.jsonl`
- `sgf-output/manifest.sqlite` as provenance context for the scrape

If the scraper output lives outside this repo, either run the scripts from a checkout
that has `sgf-output/` at the project root, symlink/copy that folder locally, or pass
explicit paths such as `--input-glob /Users/cory/Documents/sgf-scrape-test/sgf-output/jsonl/forum-11/*.jsonl`.

Tablature, paid/private lesson transcripts, and copedent-aware reasoning are intentionally out of scope for this version.

## Outputs

- `rag-data/electronics/clean_corpus.jsonl`
- `rag-data/electronics/clean_corpus_report.json`
- `rag-data/electronics/chunks.jsonl`
- `rag-data/electronics/chunk_report.json`
- `rag-data/electronics/chroma/`

## Build

Run from the project root:

```bash
python3 -m pip install -r requirements-rag.txt
python3 rag_build_clean_corpus.py
python3 rag_chunk_corpus.py
EMBEDDING_MODEL=bge-m3 python3 rag_embed_chroma.py --reset
```

Equivalent editable install:

```bash
python3 -m pip install -e ".[rag]"
```

The embedding step requires Ollama to be running locally and the embedding model to be present:

```bash
ollama pull bge-m3
ollama pull qwen3:14b
ollama serve
```

## Search

```bash
python3 rag_search.py "What are common causes of hum in a steel guitar rig?" --top-k 5
```

Each result prints the thread title, source URL, available user/date metadata, distance, and excerpt.

## Answer

```bash
python3 rag_answer.py "Should delay go in the effects loop?"
```

`rag_answer.py` retrieves local chunks and asks Ollama to answer only from those retrieved sources. If retrieval is weak, it says the corpus did not provide enough evidence instead of inventing advice.

## Streamlit App

```bash
streamlit run rag_app.py
```

The app provides a question box, answer area, source snippets, and simple filters for forum name, date text, and thread title text. Retrieved sources are shown every time.

## Test Questions

- Why does my amp buzz until I touch the changer?
- Should delay go in the effects loop?
- What do players say about Nashville 400 settings?
- What are common causes of hum in a steel guitar rig?
- What do people say about using wah for B3 sounds?
- What are common opinions about ToneX or amp modelers for steel?

## Notes

The cleaner removes obvious phpBB boilerplate such as author profile blocks, edit notices, attachment permission notices, and navigation text. It is intentionally conservative about signatures and equipment lists because those often contain useful technical details in the Electronics forum.
