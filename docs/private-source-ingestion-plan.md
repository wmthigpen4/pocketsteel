# Private Source Ingestion Plan

This plan describes the private source-inbox path before embeddings. It is intentionally separate from SGF/RAG cleanup and from public curated sources.

## Current Scope

The private source path currently has four safe stages before any real embedding run:

1. Inventory files in `source-inbox/`.
2. Normalize reviewed TXT/MD/VTT/SRT files into private JSONL.
3. Chunk normalized private documents into private chunk JSONL.
4. Run embedding preflight against the private chunks and planned private vector destination.

No app config switches, scraping, DNS changes, or deployment are part of this stage.

## Inputs And Outputs

Input to chunking:

- `corpus-private/normalized/source-inbox-documents.jsonl`

Chunk outputs:

- `corpus-private/chunks/source-inbox-chunks.jsonl`
- `corpus-private/reports/source-inbox-chunk-report.md`

Embedding preflight output:

- `corpus-private/reports/private-source-embed-preflight.md`

Planned private vector destination:

- `corpus-private/vector-stores/chroma`
- collection: `steel_guitar_private_sources_v1`

Embedding report path when a dry run or approved real run is executed:

- `corpus-private/reports/private-source-embedding-report.md`

`corpus-private/` is generated private corpus output and must remain ignored by git.

## Chunking Rules

- Preserve document boundaries.
- Preserve lesson, transcript, and rules-note boundaries.
- Do not mix unrelated files.
- Skip rows where `embedding_allowed` is `false`.
- Keep private visibility metadata on every chunk.
- Preserve tab-heavy spacing by splitting on lines instead of reflowing tab-like text.
- Include enough source metadata for future private source cards.
- Do not embed chunks until a separate explicit approval.

## Chunk Schema

Each private chunk includes:

- `chunk_id`
- `source_id`
- `source_system`
- `visibility`
- `source_path`
- `title`
- `file_type`
- `document_index`
- `chunk_index`
- `text`
- `source_url`
- `provenance_status`
- `redistribution_allowed`
- `embedding_allowed`
- `answer_quote_allowed`
- `chunk_role`
- `quality_score`
- `noise_score`
- `char_count`
- `token_estimate`
- `metadata`
- `created_at`

## Review Before Embedding

Before any private embeddings are built, review:

- source provenance records,
- normalized text quality,
- chunk reports,
- tiny/empty chunk warnings,
- answer quote permissions,
- visibility and access policy.

Private chunks should never be exposed to public/free users unless rights and access policy explicitly allow it.

## Embedding Safety

The private embedding script must:

- run private source preflight before embedding,
- require `--confirm-preflight-pass` for a real embedding run,
- support `--dry-run`,
- write only to `corpus-private/vector-stores/chroma`,
- use the `steel_guitar_private_sources_v1` collection,
- refuse SGF v1/v2 vector paths,
- preserve private metadata on every vector,
- avoid logging private source text,
- require `--reset-private-collection` before deleting/recreating the private collection.

Dry-run command:

```bash
.venv/bin/python scripts/embed_private_sources_chroma.py --dry-run
```

Real embedding command, after reviewing preflight:

```bash
.venv/bin/python scripts/embed_private_sources_chroma.py --confirm-preflight-pass
```

Private search smoke commands, after embedding:

```bash
.venv/bin/python scripts/search_private_sources.py --query "What is my E9 copedent?"
.venv/bin/python scripts/search_private_sources.py --query "What does A+F do?"
.venv/bin/python scripts/search_private_sources.py --query "What is the 10th string on E9?"
.venv/bin/python scripts/search_private_sources.py --query "What are my common grips?"
```

By default, private search output is metadata-only. Add `--show-excerpts` only when intentionally inspecting private text locally.

## Future Steps

1. Add private-source eval samples.
2. Add private-source access-control gates.
3. Add private source retrieval mode.
4. Build a private-only embedding store only after explicit approval.
5. Add admin/dev diagnostics for source lane selection.
