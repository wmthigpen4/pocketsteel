# Curated Guidance Ingestion Spike

## Task Summary

Requested: build a small ingestion spike for local markdown teaching summaries in `/Users/cory/Documents/vtt-test/guidance-cleaned`, exporting normalized JSONL and validating quality without ingesting raw lesson transcripts or blending the data into SGF/forum retrieval.

Completed:
- Created `scripts/ingest/build_curated_guidance_corpus.py`.
- Created `scripts/ingest/validate_curated_guidance_corpus.py`.
- Ran both scripts against the local `guidance-cleaned` folder.
- Produced ignored private/local JSONL and validation reports.
- Created this completion handoff and the inventory handoff.

Intentionally not changed:
- No SGF scraper changes.
- No Chroma/vector store writes.
- No embeddings.
- No production answer routing or UI wiring.
- No source-inbox/provenance changes.
- No raw transcript ingestion.
- No token-heavy prompt patching.

## Files Changed

Created:
- `scripts/ingest/build_curated_guidance_corpus.py`
- `scripts/ingest/validate_curated_guidance_corpus.py`
- `docs/handoffs/task-completions/curated-guidance-inventory.md`
- `docs/handoffs/task-completions/curated-guidance-ingestion-spike.md`

Generated ignored/private artifacts:
- `corpus-private/curated-guidance/normalized/curated-guidance-documents.jsonl`
- `corpus-private/reports/curated-guidance-inventory-full.md`
- `corpus-private/reports/curated-guidance-validation.md`
- `corpus-private/reports/curated-guidance-validation.json`

The generated `corpus-private/` artifacts should not be committed.

## Source Folder

Resolved source folder:

```text
/Users/cory/Documents/vtt-test/guidance-cleaned
```

Fallback path was not needed:

```text
/Users/cory/Document/vtt-test/guidance-cleaned
```

## Files Found / Processed / Skipped

- Markdown files found: 899.
- Files processed: 899.
- Files skipped: 0.

Top-level distribution:

| Top-level path | Markdown files |
| --- | ---: |
| `summary-draft/` | 580 |
| `full-draft/` | 303 |
| `samples/` | 6 |
| `summary-prototype/` | 5 |
| `spec/` | 3 |
| root confirmation markdown files | 2 |

## Normalized JSONL Schema

Each row uses this schema:

```json
{
  "content_layer": "curated_guidance",
  "visibility": "private_review",
  "source_path": "...",
  "source_filename": "...",
  "source_sha256": "...",
  "title": "...",
  "body": "...",
  "word_count": 0,
  "topics": [],
  "technique_tags": [],
  "instrument": "unknown|E9|C6|non_pedal|general",
  "strings": [],
  "pedals_levers": [],
  "frets": [],
  "keys": [],
  "difficulty": "unknown|beginner|intermediate|advanced",
  "needs_review": true,
  "quality_flags": []
}
```

Notes:
- `content_layer` is always `curated_guidance`.
- `visibility` is always `private_review`.
- `needs_review` is always `true`.
- This layer is deliberately separate from SGF/forum content.

## Validation Summary

Validation result:
- Rows: 899.
- Structural failures: 0.
- Warnings: 972.

Word count stats:
- min: 36
- max: 15601
- avg: 594.72

Instrument counts:

| Instrument | Rows |
| --- | ---: |
| `unknown` | 776 |
| `general` | 70 |
| `E9` | 37 |
| `C6` | 8 |
| `non_pedal` | 8 |

Difficulty counts:

| Difficulty | Rows |
| --- | ---: |
| `unknown` | 453 |
| `beginner` | 315 |
| `intermediate` | 87 |
| `advanced` | 44 |

Quality flag counts:

| Quality flag | Count |
| --- | ---: |
| `possible_duplicate_files_by_hash` | 362 |
| `body_under_100_words` | 279 |
| `no_steel_specific_terms` | 232 |
| `missing_topic_tags` | 227 |
| `contains_player_should_phrase` | 130 |
| `body_over_reasonable_chunk_size` | 57 |
| `first_person_instructor_phrasing` | 37 |

Duplicate hash groups: 10.

## Redacted Example Rows

The body field is intentionally redacted here to avoid putting private-review teaching text into a tracked handoff. The ignored JSONL has the actual normalized bodies.

```json
{
  "content_layer": "curated_guidance",
  "visibility": "private_review",
  "source_path": "all_transcripts_pre_embedding_cleanup_confirmation.md",
  "source_filename": "all_transcripts_pre_embedding_cleanup_confirmation.md",
  "source_sha256": "4c811d301711...",
  "title": "All-Transcript Pre-Embedding Cleanup Confirmation",
  "body": "<private_review body omitted from handoff preview>",
  "word_count": 322,
  "topics": ["blocking", "copedent", "grips", "tone"],
  "technique_tags": ["pedal movement"],
  "instrument": "unknown",
  "strings": [],
  "pedals_levers": [],
  "frets": [],
  "keys": [],
  "difficulty": "unknown",
  "needs_review": true,
  "quality_flags": []
}
```

```json
{
  "content_layer": "curated_guidance",
  "visibility": "private_review",
  "source_path": "final_pre_embedding_cleanup_confirmation.md",
  "source_filename": "final_pre_embedding_cleanup_confirmation.md",
  "source_sha256": "521c391b1f6a...",
  "title": "Final Pre-Embedding Cleanup Confirmation",
  "body": "<private_review body omitted from handoff preview>",
  "word_count": 323,
  "topics": ["fills"],
  "technique_tags": [],
  "instrument": "unknown",
  "strings": [],
  "pedals_levers": [],
  "frets": [],
  "keys": [],
  "difficulty": "unknown",
  "needs_review": true,
  "quality_flags": ["no_steel_specific_terms"]
}
```

```json
{
  "content_layer": "curated_guidance",
  "visibility": "private_review",
  "source_path": "full-draft/by-source/<source-id-and-title>/guidance_draft.md",
  "source_filename": "guidance_draft.md",
  "source_sha256": "d35792cabb36...",
  "title": "Dry-Run Guidance Draft",
  "body": "<private_review body omitted from handoff preview>",
  "word_count": 685,
  "topics": ["copedent", "fills", "tone"],
  "technique_tags": ["pedal movement"],
  "instrument": "unknown",
  "strings": [],
  "pedals_levers": ["A", "B", "C"],
  "frets": [],
  "keys": ["B", "C"],
  "difficulty": "beginner",
  "needs_review": true,
  "quality_flags": []
}
```

## Retrieval / Evaluation Test Plan

Do not wire this layer into production retrieval yet. Recommended next spike:

1. Add a private, offline eval fixture that reads `content_layer=curated_guidance` rows from ignored JSONL.
2. Select 20-30 reviewed rows with low/no quality flags.
3. Create query expectations for teaching-guidance needs, for example:
   - technique explanation,
   - practice drill,
   - lick concept,
   - chord movement,
   - tone/setup guidance.
4. Compare candidate retrieval against SGF-only retrieval, but keep result sets separate:
   - `sgf_forum`
   - `curated_guidance`
   - future blended mode only after review.
5. Require source cards to label `content_layer=curated_guidance` and `visibility=private_review`.
6. Do not promote any row to public/user-visible retrieval until rights and visibility are reviewed.

## Tests And Checks

Commands run:

```bash
git status --short
test -d "$HOME/Documents/vtt-test/guidance-cleaned"
find "$HOME/Documents/vtt-test/guidance-cleaned" -type f -name '*.md' | wc -l
.venv/bin/python -m py_compile scripts/ingest/build_curated_guidance_corpus.py scripts/ingest/validate_curated_guidance_corpus.py
.venv/bin/python scripts/ingest/build_curated_guidance_corpus.py
.venv/bin/python scripts/ingest/validate_curated_guidance_corpus.py
git diff --check
```

Results:
- Source folder found.
- Markdown files found: 899.
- Build script: processed 899 rows, skipped 0.
- Validation script: 0 failures, 972 warnings.
- `py_compile`: passed.
- `git diff --check`: passed.

## Git Status Summary

This task adds two scripts and two tracked handoff reports. The repo already had broad unrelated dirty/parked files before this task.

Safe-to-stage files for this spike:
- `scripts/ingest/build_curated_guidance_corpus.py`
- `scripts/ingest/validate_curated_guidance_corpus.py`
- `docs/handoffs/task-completions/curated-guidance-inventory.md`
- `docs/handoffs/task-completions/curated-guidance-ingestion-spike.md`

Files that should not be committed:
- `corpus-private/curated-guidance/normalized/curated-guidance-documents.jsonl`
- `corpus-private/reports/curated-guidance-inventory-full.md`
- `corpus-private/reports/curated-guidance-validation.md`
- `corpus-private/reports/curated-guidance-validation.json`
- raw markdown files under `/Users/cory/Documents/vtt-test/guidance-cleaned`
- any Chroma/vector store, embedding output, corpus-v2, source-inbox, private source, deploy, DNS, auth, or scraping output.

## Risk Assessment

Risk: medium.

Why:
- Scripts are local/offline and do not touch production retrieval, but they process private-review derived teaching material.
- The generated JSONL contains private-review bodies and must remain ignored/uncommitted.
- Topic/instrument/difficulty inference is heuristic and should be treated as review assistance, not final metadata.

Rollback:
- Remove the two `scripts/ingest/` files and the two tracked handoffs.
- Delete ignored generated artifacts under `corpus-private/curated-guidance/` and `corpus-private/reports/curated-guidance-*` if desired.

## Commit Readiness

Needs human review first.

The script and handoff files are safe to review, but this is a new ingestion spike touching private-review content workflows. Commit only the safe-to-stage files listed above, never the generated private artifacts.

## Suggested Next Step

Lane 15 QA / Answer Eval:

```text
Review the curated-guidance ingestion spike. Read docs/handoffs/task-completions/curated-guidance-ingestion-spike.md and inspect the scripts under scripts/ingest/. Validate that generated corpus-private outputs stay ignored, quality flags are useful, and no SGF/forum retrieval or production answer routing is changed. Recommend the smallest offline retrieval/eval fixture for curated_guidance rows, but do not wire the layer into production UI or Chroma.
```
