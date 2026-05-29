# Source Ingestion Policy

This policy covers non-SGF source files staged in `source-inbox/` before they are normalized, chunked, embedded, or used by The Turnaround.

The first rule is provenance before ingestion. A file being in `source-inbox/` does not mean it is approved for embeddings, public answers, quotation, redistribution, or product use.

## Required Provenance Fields

Each source must have a provenance record with:

- `source_id`
- `path`
- `title`
- `author_or_creator`
- `source_type`
- `source_system`
- `visibility`: `private`, `public`, or `review`
- `redistribution_allowed`: `true`, `false`, or `unknown`
- `embedding_allowed`: `true`, `false`, or `review`
- `answer_quote_allowed`: `true`, `false`, or `limited`
- `source_url` if applicable
- `notes`
- `reviewed_at`
- `reviewed_by`

## Default Rules

1. Private, paid, member-only, or lesson material defaults to `private`.
2. Private material may be embedded only for private personal use unless rights explicitly allow broader use.
3. Private material must not be exposed to public, anonymous, free, or unauthorized users.
4. Unknown rights default to `review` visibility and private handling.
5. User-authored personal notes and rules can be used when the user confirms authorship and intended use.
6. Curated links belong in `corpus_metadata/source_registry.json`, not in the vector corpus.
7. PDFs are not normalized by the TXT/VTT normalizer yet. They require a separate review/extraction step.

## Source-Inbox Lanes

| Folder | Default source system | Default visibility | Notes |
| --- | --- | --- | --- |
| `source-inbox/private-lessons/` | `private_lesson_transcript` | `private` | Paid/private lessons and personal teaching material. |
| `source-inbox/public-reference/` | `public_reference` | `review` | Public web/reference text saved for review. |
| `source-inbox/manuals/` | `steel_manual` | `review` | Manuals require rights/provenance review. |
| `source-inbox/pdfs/` | `pdf_reference` | `review` | Metadata only for now; no normalization in this phase. |
| `source-inbox/transcripts/` | `transcript` | `review` | VTT/SRT/TXT transcripts require source and rights review. |
| `source-inbox/rules/` | `personal_rules_note` | `private` | User-authored rules may become rules-layer content. |
| `source-inbox/curated-sources/` | `curated_source_candidate` | `review` | Convert to curated registry entries instead of embedding by default. |
| `source-inbox/pending-review/` | `pending_review` | `review` | Human review required before routing. |

## Normalization Rules

The source-inbox normalizer may process only:

- `.txt`
- `.md`
- `.vtt`
- `.srt`

It must skip:

- PDFs
- DOCX files for now
- unsupported binary files
- files without provenance records
- files whose provenance says `embedding_allowed: false`
- curated source candidates that belong in the source registry

The normalizer writes generated private outputs under `corpus-private/`, which must remain ignored by git.

## Answer And Embedding Permissions

`embedding_allowed` controls whether normalized text may proceed toward private embedding later. This normalizer can prepare records with `embedding_allowed: true` or `review`, but embedding is a separate approval step.

`answer_quote_allowed` controls whether answer generation may quote the source:

- `true`: quoting is allowed within normal answer limits.
- `limited`: paraphrase by default; quote only short excerpts when necessary.
- `false`: do not quote in answer text; use only for private retrieval or internal summarization when allowed.

`redistribution_allowed` controls whether the source text can be redistributed. Unknown or false redistribution does not automatically forbid private personal embeddings, but it does forbid public exposure unless rights are later clarified.

## Generated Outputs

The normalizer writes:

- `corpus-private/normalized/source-inbox-documents.jsonl`
- `corpus-private/reports/source-inbox-normalize-skipped.md`

These files are generated private corpus artifacts. Do not commit them.
