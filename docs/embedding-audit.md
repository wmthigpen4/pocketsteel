# SGF Embedding Audit

Audit date: 2026-05-27

Scope: read-only audit of the completed unified SGF Chroma embedding run. No embeddings were rerun, no vector data was reset or deleted, and no live SGF scraping was run.

## Summary
- Chroma path: `$STEEL_RAG_CHROMA_PATH`
- Chroma SQLite: `$STEEL_RAG_CHROMA_PATH/chroma.sqlite3`
- Collection(s): `steel_guitar_unified`
- Chunk file: `$STEEL_RAG_CHUNKS_PATH`
- Embedded vectors: `401,100`
- Stored documents/excerpts: `401,100`
- Chunk rows: `401,100`
- Vector/chunk count match: `yes`

## Chroma Metadata
| key | present | nonempty | missing |
| --- | ---: | ---: | ---: |
| `forum_name` | 401,100 | 401,100 | 0 |
| `thread_title` | 401,100 | 401,100 | 0 |
| `thread_url` | 401,100 | 401,100 | 0 |
| `post_uid` | 0 | 0 | 401,100 |
| `chunk_id` | 401,100 | 401,100 | 0 |
| `chroma:document` | 401,100 | 401,100 | 0 |

## Chunk File Fields
| key | present | empty/missing |
| --- | ---: | ---: |
| `forum_name` | 401,100 | 0 |
| `thread_title` | 401,100 | 0 |
| `thread_url` | 401,100 | 0 |
| `post_uid` | 0 | 401,100 |
| `post_uids` | 401,100 | 148 |
| `chunk_id` | 401,100 | 0 |
| `text` | 0 | 401,100 |
| `chunk_text` | 401,100 | 0 |

## Compatibility Checks
| expectation | compatibility rule | passing rows | missing rows |
| --- | --- | ---: | ---: |
| post identity | scalar `post_uid` or nonempty `post_uids` | 400,952 | 148 |
| source text | `text`, `chunk_text`, or Chroma document content | 401,100 | 0 |
| chunk identity | nonempty `chunk_id` | 401,100 | 0 |

## Source Systems
- `sgf_phpbb_current`: `332,982`
- `sgf_ubb_legacy`: `68,118`

## Metadata Notes
- Chroma metadata does not include scalar `post_uid`; approved compatibility treats `chunk_id` as the vector-level required identity.
- Approved compatibility treats nonempty `post_uids` arrays as post identity when scalar `post_uid` is missing.
- Approved compatibility treats `chunk_text` and Chroma document content as source text when `text` is missing.

## Readiness
- Technical retrieval readiness: `yes`, for smoke retrieval against the existing Chroma store.
- Smoke retrieval result: `passed` for source lookup, citation metadata, and excerpt display.
- Final status: `YELLOW - approved for retrieval/API integration with known risks, not production-quality signoff`.
- Final quality readiness: `not production-ready`; chunk-quality flags are triaged in [chunk-quality-triage.md](chunk-quality-triage.md), but Phase 3 cleanup/rebuild is not approved.

## Pass Status
Overall audit status: `YELLOW - approved for retrieval/API integration with known risks, not production-quality signoff`.

Passing checks:

- Vector DB path identified.
- Source chunk file identified.
- Vector count and chunk count both equal `401,100`.
- Chroma has source text/excerpts for every vector.
- Chroma has `forum_name`, `thread_title`, `thread_url`, and `chunk_id` for every vector.
- Smoke retrieval returned relevant source threads with URLs and excerpts.

Known risks:

- Chroma does not include scalar `post_uid`; it relies on `chunk_id`.
- Chunk records use `post_uids` arrays instead of scalar `post_uid`; `148` rows have empty/missing `post_uids`.
- Chunk source text is named `chunk_text`, not `text`. This works for Chroma and approved compatibility, but any downstream code expecting `text` must handle the field alias.
- Chunk quality is triaged but not fixed because Phase 3 is not approved.

Chunk issue counts:

- `junk_phrase`: `46,735`
- `tiny_chunk`: `9,058`
- `huge_chunk`: `4,889`
- `very_tiny_chunk`: `839`

Phase 2 primary triage buckets:

- `false positives`: `43,629`
- `low-value tiny chunks`: `10,455`
- `oversized chunks`: `3,788`
- `duplicated/repeated text`: `128`
- `mostly quotes`: `48`
- `mostly links`: `1,670`
- `missing metadata`: `29`
- `possible mixed-topic chunks`: `1,774`

Production pass condition: Phase 3 cleanup/rebuild is approved, the corpus and vector store are refreshed, and this audit is rerun with remaining metadata and chunk-quality risks resolved or explicitly accepted for production.

## Retrieval Smoke Test
These searches used `search_unified_rag.py` against the completed Chroma store with `bge-m3` query embeddings. They did not rebuild, reset, delete, or repopulate vector data.

| query | result |
| --- | --- |
| `What are common uses for the E9 9th string?` | Passed. Top results included direct Pedal Steel threads about 9th-string lowers, D-to-Db lever uses, and a thread titled `9th string uses`. |
| `How do steel players reduce hum in an amplifier?` | Passed with caveat. Top results included direct Electronics threads about single-coil hum/noise; lower-ranked results drifted into amp loudness/headroom topics. |
| `What speaker works well in a Nashville 400?` | Passed. Top results included direct Electronics threads about Nashville 400 speaker options and speaker changes. |

Smoke-test metadata checks:

- Returned results include `forum_name`.
- Returned results include `thread_title`.
- Returned results include `thread_url`.
- Returned results include stored document excerpts.
- Results span both `sgf_phpbb_current` and `sgf_ubb_legacy` where relevant.

## Commands
- `export STEEL_RAG_CORPUS_ROOT=/path/to/corpus-unified`
- `export STEEL_RAG_CHROMA_PATH="$STEEL_RAG_CORPUS_ROOT/vector-stores/chroma"`
- `export STEEL_RAG_CHUNKS_PATH="$STEEL_RAG_CORPUS_ROOT/chunks.jsonl"`
- `find "$STEEL_RAG_CORPUS_ROOT" -maxdepth 4 -type f \( -name 'chroma.sqlite3' -o -name 'chunks.jsonl' -o -name '*.jsonl' -o -name '*.json' \) -print | sort`
- `sqlite3 "$STEEL_RAG_CHROMA_PATH/chroma.sqlite3" '.tables'`
- `sqlite3 "$STEEL_RAG_CHROMA_PATH/chroma.sqlite3" "select name, id from collections;"`
- `sqlite3 "$STEEL_RAG_CHROMA_PATH/chroma.sqlite3" "select count(*) from embeddings; select count(distinct embedding_id) from embeddings; select count(*) from embedding_fulltext_search_content;"`
- `wc -l "$STEEL_RAG_CHUNKS_PATH"`
- `python3 scripts/sgf_embedding_audit.py --chroma "$STEEL_RAG_CHROMA_PATH" --chunks "$STEEL_RAG_CHUNKS_PATH" --output docs/embedding-audit.md`
- `python3 -m py_compile scripts/sgf_embedding_audit.py`
- `python3 search_unified_rag.py "What are common uses for the E9 9th string?" --embedding-model bge-m3 --n-results 5`
- `python3 search_unified_rag.py "How do steel players reduce hum in an amplifier?" --embedding-model bge-m3 --n-results 5`
- `python3 search_unified_rag.py "What speaker works well in a Nashville 400?" --embedding-model bge-m3 --n-results 5`
- `awk -F '\t' 'NR>1 {count[$1]++} END {for (k in count) print k, count[k]}' "$STEEL_RAG_CORPUS_ROOT/reports/unified_chunk_issues.tsv" | sort`
- `awk -F '\t' 'NR>1 {count[$1 "\t" $4]++} END {for (k in count) print k "\t" count[k]}' "$STEEL_RAG_CORPUS_ROOT/reports/unified_chunk_issues.tsv" | sort`
- `awk -F '\t' 'NR>1 {count[$5]++} END {for (k in count) print count[k] "\t" k}' "$STEEL_RAG_CORPUS_ROOT/reports/unified_chunk_issues.tsv" | sort -nr | head -20`
- `python3 scripts/sgf_chunk_quality_triage.py --issues "$STEEL_RAG_CORPUS_ROOT/reports/unified_chunk_issues.tsv" --output docs/chunk-quality-triage.md`
