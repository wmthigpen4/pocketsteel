# Phase 3C Chunker V2 Report

Scope: implement and test a sample-safe chunker-v2 for corpus-v2 preparation. This phase consumes Phase 3B cleaned/classified records and emits sample retrieval chunks only. It does not run a full corpus rebuild and does not embed anything.

## What Changed

- Added `scripts/phase3_chunk_v2.py`.
- Added focused tests in `tests/test_phase3_chunk_v2.py`.
- Generated sample output only under `/tmp/steel-rag-corpus-v2-sample/`.

The chunker reads Phase 3B records with `answer_text`, `chunk_role`, `post_role`, quality fields, cleanup flags, source metadata, and post identity. It writes sample chunk-v2 JSONL records with:

- `chunk_id`
- `source_system`
- `forum_name`
- `thread_id`
- `thread_title`
- `source_url`
- `post_uids`
- `chunk_text`
- `chunk_role`
- `post_role_summary`
- `quality_score`
- `noise_score`
- `cleanup_flags`
- `source_metadata_complete`

## Chunking Rules Implemented

- Preserves source metadata and post identity from Phase 3B records.
- Builds deterministic `chunk_id` values from thread, role, source record IDs, and chunk text.
- Prefers `answer_advice` records for answer chunks.
- Keeps unpaired question-only records as `question` chunks with `question_unpaired`.
- Intentionally pairs a nearby question with a following answer when they fit within `max_words`, marking `question_paired`.
- Excludes `contact_block`, `gear_signature`, `link_only`, `sale_wanted`, and `joke_chatter` from answer chunks.
- Splits oversized answer text by word count and marks `oversized_split`.
- Skips tiny low-value excluded-role chunks while allowing short answer/question records to survive with flags when needed.
- Flags answer records that carry extra role signals as `mixed_topic_flagged`.
- Flags quote-marker content as `quote_heavy_flagged`.

## Sample Output

Sample output path:

```text
/tmp/steel-rag-corpus-v2-sample/chunks-v2.jsonl
```

Sample command:

```bash
.venv/bin/python scripts/phase3_clean_classify_chunks.py \
  --input tests/fixtures/phase3_sample_chunks.jsonl \
  --output /tmp/steel-rag-corpus-v2-sample/clean_classified_chunks.jsonl \
  --report /tmp/steel-rag-corpus-v2-sample/phase3b-report.md

.venv/bin/python scripts/phase3_chunk_v2.py \
  --input /tmp/steel-rag-corpus-v2-sample/clean_classified_chunks.jsonl \
  --output /tmp/steel-rag-corpus-v2-sample/chunks-v2.jsonl \
  --report /tmp/steel-rag-corpus-v2-sample/phase3c-report.md \
  --target-words 80 \
  --max-words 100 \
  --min-words 4
```

Sample chunk role counts:

| role | count |
| --- | ---: |
| `answer_advice` | 1 |
| `question` | 1 |

Sample cleanup flag counts:

| cleanup flag | count |
| --- | ---: |
| `duplicate_sentence_removed` | 1 |
| `question_unpaired` | 1 |
| `top_removed` | 1 |

Sample averages:

- Average noise score: `0.195`
- Average quality score: `0.596`

## Sample Before And After Chunk Examples

### Answer/Advice Chunk

Phase 3B input record:

```text
Rick / 1 Jan 2007 1:00 pm Try a grounded outlet first.
```

Chunk-v2 output:

```text
Rick / 1 Jan 2007 1:00 pm Try a grounded outlet first.
```

Output role: `answer_advice`

Output flags: `duplicate_sentence_removed`, `top_removed`

Output post IDs: `p1`

### Question Chunk

Phase 3B input record:

```text
Does anyone know what speaker came in a Sho-Bud Compactra amp?
```

Chunk-v2 output:

```text
Does anyone know what speaker came in a Sho-Bud Compactra amp?
```

Output role: `question`

Output flags: `question_unpaired`

Output post IDs: `p4`

### Excluded Low-Value Roles

The sample input included `contact_block`, `gear_signature`, and `sale_wanted` records. The chunker did not promote those into answer chunks. They remain available in Phase 3B classified output but are excluded from sample answer-oriented chunk-v2 output.

## Tests

Targeted test command:

```bash
.venv/bin/python -m pytest tests/test_phase3_clean_classify_chunks.py tests/test_phase3_chunk_v2.py
```

Result: `20 passed`.

Full test command:

```bash
.venv/bin/python -m pytest
```

Result: `125 passed`.

## Known Limits

- This is still sample-safe and does not run against the full unified corpus.
- The current pairing logic is local and conservative; Phase 3D should not embed until a larger v2 sample review confirms that question/answer pairing behaves well across real threads.
- The splitter is word-count based, not semantic. It is suitable for sample validation, but a production chunker may want sentence-aware boundaries and better author/date handling.
- Excluded roles are omitted from answer chunks rather than emitted to a separate review stream. A future full pipeline may want separate `review_chunks.jsonl`.

## Recommended Phase 3D Embed-V2 Planning Prompt

```text
Begin Phase 3D embed-v2 planning for The Turnaround corpus-v2.

This is YELLOW/RED-adjacent and must stop after a plan unless explicitly approved to create a new vector store.

Use:
- docs/phase-3-corpus-cleanup-plan.md
- docs/phase-3a-corpus-profile.md
- docs/phase-3b-cleaner-classifier-report.md
- docs/phase-3c-chunker-v2-report.md
- scripts/phase3_clean_classify_chunks.py
- scripts/phase3_chunk_v2.py

Do not modify v1 Chroma, reset Chroma, regenerate embeddings, delete corpus files, run live SGF scraping, overwrite corpus-unified/chunks.jsonl, change backend answer code, change frontend code, or switch app config.

Plan an embed-v2 workflow that writes only beside v1, under corpus-v2/vector-stores/chroma, with a new collection name such as steel_guitar_unified_v2. Include preflight checks, sample validation, metadata schema, rollback/cleanup guardrails, and an A/B eval handoff. Do not embed anything until explicitly approved.

End with files changed, tests run, risks, human decision needed, recommended next step, and explicit confirmation that v1 Chroma was not modified.
```

## Current V1 Chroma Statement

The current v1 Chroma store was not modified. This Phase 3C work did not reset Chroma, regenerate embeddings, delete corpus files, run live SGF scraping, overwrite `corpus-unified/chunks.jsonl`, change backend answer code, change frontend code, switch app config, or run a full corpus rebuild.
