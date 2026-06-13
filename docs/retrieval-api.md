# Retrieval API

The local retrieval API reads from an existing Chroma vector DB. It must not
scrape SGF, rebuild embeddings, reset Chroma, modify vector data, or copy the
vector DB into this app repo.

For local development, point the app at the completed Chroma store:

```bash
export STEEL_RAG_CHROMA_PATH="~/Documents/sgf-scrape-test/corpus-unified/vector-stores/chroma"
```

The completed unified store currently uses this Chroma collection:

```bash
export STEEL_RAG_CHROMA_COLLECTION="steel_guitar_unified"
```

`STEEL_RAG_CHROMA_PATH` is preferred over the app-local fallback path
`rag-data/electronics/chroma`. The API keeps that fallback only for older local
setups.

Run the API:

```bash
python3 rag_api.py --port 8765
```

Search endpoint:

```text
GET /api/search?q=Fender+Steel+King+settings
```

Each result is normalized to:

- `score`
- `excerpt`
- `forum_name`
- `thread_title`
- `thread_url`
- `chunk_id`
- `post_uid`
- `warnings`

Warnings identify metadata fallbacks, such as using `source_url` for
`thread_url`, `chunk_text` for text, the Chroma id for `chunk_id`, or the first
`post_uids` item for `post_uid`.
