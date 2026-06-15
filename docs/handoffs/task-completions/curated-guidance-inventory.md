# Curated Guidance Inventory

## Task Summary

Requested: inventory markdown guidance summaries from the local `guidance-cleaned` folder for a curated teaching-guidance ingestion spike.

Completed:
- Confirmed the source folder exists at `/Users/cory/Documents/vtt-test/guidance-cleaned`.
- Found 899 markdown files.
- Wrote a full private/local inventory to an ignored report path:
  - `corpus-private/reports/curated-guidance-inventory-full.md`

Intentionally not changed:
- No SGF scraper changes.
- No production answer routing changes.
- No Chroma/vector store, embeddings, corpus-v2, source-inbox, deployment, DNS, auth, UI, or prompt patches.
- No raw/private body text is included in this tracked handoff.

## Inventory Summary

Source root:

```text
/Users/cory/Documents/vtt-test/guidance-cleaned
```

Markdown files found: 899

Top-level distribution:

| Top-level path | Markdown files |
| --- | ---: |
| `summary-draft/` | 580 |
| `full-draft/` | 303 |
| `samples/` | 6 |
| `summary-prototype/` | 5 |
| `spec/` | 3 |
| `all_transcripts_pre_embedding_cleanup_confirmation.md` | 1 |
| `final_pre_embedding_cleanup_confirmation.md` | 1 |

Sample path forms:

```text
all_transcripts_pre_embedding_cleanup_confirmation.md
final_pre_embedding_cleanup_confirmation.md
full-draft/by-source/<source-id-and-title>/guidance_draft.md
summary-draft/...
samples/...
summary-prototype/...
spec/...
```

The full per-file inventory is intentionally stored in the ignored private report, not copied into this tracked handoff, because the filenames and titles are private-review source metadata.

## Private Inventory Artifact

Full inventory path:

```text
corpus-private/reports/curated-guidance-inventory-full.md
```

That report includes:
- relative source path,
- inferred title,
- word count,
- quality flags.

It should not be committed unless a future lane explicitly approves committing private-review metadata.

## Integration Notes

- Treat every row as `content_layer=curated_guidance`.
- Treat every row as `visibility=private_review`.
- This layer is separate from SGF/forum retrieval and must not be blended into SGF corpus files.
- These files are summarized guidance notes, not raw lesson transcript ingestion.

## Tests And Checks

Commands run:

```bash
test -d "$HOME/Documents/vtt-test/guidance-cleaned"
find "$HOME/Documents/vtt-test/guidance-cleaned" -type f -name '*.md' | wc -l
.venv/bin/python scripts/ingest/build_curated_guidance_corpus.py
.venv/bin/python scripts/ingest/validate_curated_guidance_corpus.py
git diff --check
```

Results:
- Source folder exists.
- Markdown files found: 899.
- Build processed: 899 rows, 0 skipped.
- Validation: 0 failures, 972 warnings.
- `git diff --check`: passed.

## Commit Readiness

Needs human review first.

Reason:
- The scripts and tracked handoffs are safe to review.
- Generated `corpus-private/` artifacts contain private-review metadata and derived content and must remain unstaged.

## Suggested Next Step

Lane 15 QA / Answer Eval:

```text
Review the curated-guidance inventory and validation reports. Confirm whether the quality flags are useful enough for a private-review promotion workflow. Do not embed or wire into production retrieval. Focus on whether the next slice should add chunking/eval fixtures for `content_layer=curated_guidance`.
```
