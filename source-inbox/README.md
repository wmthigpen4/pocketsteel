# Source Inbox

Use this folder as a human-managed intake area for future non-SGF content before anything is normalized, chunked, embedded, or added to The Turnaround.

Raw source files may be dropped into the matching subfolder for review:

- `rules/`: personal or project rules that may become a rules layer.
- `curated-sources/`: official links, source lists, and vendor/reference candidates.
- `private-lessons/`: private, paid, member-only, or lesson transcript material.
- `public-reference/`: public web/reference material saved for review.
- `manuals/`: manuals or official product documentation.
- `pdfs/`: PDF files awaiting review or OCR.
- `transcripts/`: VTT, SRT, TXT, or other transcript files.
- `pending-review/`: files whose lane is not clear yet.

Do not commit raw source documents by default. Private lessons, paid transcripts, member-only content, credentials, and personal material must stay private unless rights and provenance explicitly allow sharing.

Classify each file before embedding. Decide whether it belongs in the rules layer, curated source registry, RAG ingestion, personal profile data, legal/provenance review, or ignore/generated/test material.

Accepted intake formats include `.txt`, `.pdf`, `.vtt`, `.srt`, and `.docx`. Generated normalized corpus files, chunks, embedding outputs, Chroma/vector stores, reports, and review queues belong in ignored generated-output locations, not in this inbox.
