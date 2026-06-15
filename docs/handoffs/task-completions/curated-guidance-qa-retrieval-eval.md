# Curated Guidance QA Retrieval Eval

## Task Summary

Requested: review the curated-guidance ingestion spike, review validation warnings, and create a small offline retrieval/eval fixture for `content_layer=curated_guidance`.

Completed:
- Reviewed `scripts/ingest/build_curated_guidance_corpus.py` for path handling, schema, and commit safety.
- Reviewed `scripts/ingest/validate_curated_guidance_corpus.py` and the generated validation reports.
- Added `scripts/eval/eval_curated_guidance_retrieval.py`, a local keyword/BM25-style retrieval fixture for curated guidance only.
- Ran the fixture against `corpus-private/curated-guidance/normalized/curated-guidance-documents.jsonl`.
- Generated ignored private reports under `corpus-private/reports/`.

Intentionally not changed:
- No production UI wiring.
- No protected-preview wiring.
- No SGF retrieval blending.
- No Chroma/vector store writes.
- No embeddings.
- No hosted LLM calls or external API keys.
- No private guidance markdown bodies copied into this tracked handoff.

## Files Changed

Created:
- `scripts/eval/eval_curated_guidance_retrieval.py`
- `docs/handoffs/task-completions/curated-guidance-qa-retrieval-eval.md`

Reviewed existing/untracked spike files:
- `scripts/ingest/build_curated_guidance_corpus.py`
- `scripts/ingest/validate_curated_guidance_corpus.py`
- `docs/handoffs/task-completions/curated-guidance-inventory.md`
- `docs/handoffs/task-completions/curated-guidance-ingestion-spike.md`

Generated ignored/private artifacts:
- `corpus-private/reports/curated-guidance-retrieval-eval.md`
- `corpus-private/reports/curated-guidance-retrieval-eval.json`

Existing generated ignored/private artifacts reviewed:
- `corpus-private/curated-guidance/normalized/curated-guidance-documents.jsonl`
- `corpus-private/reports/curated-guidance-inventory-full.md`
- `corpus-private/reports/curated-guidance-validation.md`
- `corpus-private/reports/curated-guidance-validation.json`

## Ingestion Script Review

### `build_curated_guidance_corpus.py`

Safety and path handling:
- Reads local markdown from an explicit source folder or default local candidates.
- Default source is `~/Documents/vtt-test/guidance-cleaned`; fallback typo path `~/Document/vtt-test/guidance-cleaned` is harmless but should probably be cleaned later.
- Uses relative `source_path` inside rows, not absolute source paths.
- Writes only to `corpus-private/curated-guidance/normalized/` and `corpus-private/reports/`.
- Does not touch SGF corpus files, Chroma, embeddings, deployment, auth, or UI.

Schema consistency:
- Emits stable required fields matching the validator:
  - `content_layer`
  - `visibility`
  - `source_path`
  - `source_filename`
  - `source_sha256`
  - `title`
  - `body`
  - `word_count`
  - `topics`
  - `technique_tags`
  - `instrument`
  - `strings`
  - `pedals_levers`
  - `frets`
  - `keys`
  - `difficulty`
  - `needs_review`
  - `quality_flags`
- Sets `content_layer=curated_guidance`, `visibility=private_review`, and `needs_review=true` consistently.

Commit safety:
- Script is safe to commit.
- Generated `corpus-private/` outputs are not safe to commit.
- Private inventory report includes an absolute source root and source metadata, but it is ignored and should remain uncommitted.

### `validate_curated_guidance_corpus.py`

Safety and path handling:
- Reads the ignored JSONL only.
- Writes validation reports to ignored `corpus-private/reports/`.
- Redacts row bodies in markdown examples.
- Does not embed, retrieve from Chroma, or write production config.

Schema consistency:
- Required fields align with the builder.
- Validates `content_layer=curated_guidance`, `visibility=private_review`, and `needs_review=true`.
- Detects duplicate source paths, duplicate hashes, invalid enum values, and quality flags.

Commit safety:
- Script is safe to commit.
- Generated validation reports must remain uncommitted.

## Validation Warning Summary

Validation input:
- Rows: 899
- Failures: 0
- Warnings: 972
- Validation OK: true

Warning categories:

| Warning / quality flag | Count | QA interpretation |
| --- | ---: | --- |
| `possible_duplicate_files_by_hash` | 362 | Must fix before app integration. Ten duplicate hash groups account for 362 files, likely duplicate generated variants or repeated placeholder/member files. |
| `body_under_100_words` | 279 | Mostly likely placeholder, meeting/member, or low-content rows; should be filtered out of retrieval candidates. |
| `no_steel_specific_terms` | 232 | Metadata/content gap; often harmless for admin-like rows, but unsafe for retrieval promotion without filtering. |
| `missing_topic_tags` | 227 | Metadata gap; retrieval can still work by body/title keywords, but app integration should not rely on these rows without topic repair or fallback tagging. |
| `contains_player_should_phrase` | 130 | Mild style residue from generated guidance phrasing; not necessarily transcript residue, but should be reviewed before user-visible answer synthesis. |
| `body_over_reasonable_chunk_size` | 57 | Must address before embedding/app integration; these rows are too long and should be split/chunked. |
| `first_person_instructor_phrasing` | 37 | Possible instructor/lesson voice residue; review before promotion. |

Instrument distribution:
- `unknown`: 776
- `general`: 70
- `E9`: 37
- `C6`: 8
- `non_pedal`: 8

Difficulty distribution:
- `unknown`: 453
- `beginner`: 315
- `intermediate`: 87
- `advanced`: 44

Word count stats:
- min: 36
- max: 15601
- avg: 594.72

## Transcript Residue Assessment

The warnings look more like metadata/quality-gate gaps than widespread raw transcript residue.

Evidence:
- `possible_transcript_residue` did not appear in the validation flag counts.
- The dominant warnings are duplicate hashes, short bodies, missing tags, no steel-specific terms, and chunk length.
- `first_person_instructor_phrasing` appears in 37 rows and `contains_player_should_phrase` in 130 rows. These may reflect generated lesson-guidance style or instructor voice, not raw transcript timecode residue.

QA conclusion:
- The corpus is structurally valid.
- It is not ready for app retrieval integration as-is.
- Pre-integration filtering should exclude duplicate hash groups, under-100-word rows, no-steel-term rows, and overlong rows until chunking/review handles them.

## Offline Retrieval Fixture

Created:
- `scripts/eval/eval_curated_guidance_retrieval.py`

Behavior:
- Reads `corpus-private/curated-guidance/normalized/curated-guidance-documents.jsonl`.
- Requires rows to have `content_layer=curated_guidance`.
- Uses local keyword/BM25-style scoring with title/path/metadata/body weighting.
- Uses a hand-authored expected-topic map for 10 teaching queries.
- Outputs top 5 results per query.
- Reports title, source filename, score, matched terms, content layer, visibility, quality flags, a 500-character capped excerpt, and usefulness.
- Does not call hosted LLMs.
- Does not require external API keys.
- Does not touch Chroma, embeddings, production app config, or SGF retrieval.

Generated:
- `corpus-private/reports/curated-guidance-retrieval-eval.md`
- `corpus-private/reports/curated-guidance-retrieval-eval.json`

## Retrieval Eval Results

Eval input:
- Rows searched: 899
- Queries: 10
- Top-k per query: 5

Summary:
- Top-3 usefulness counts: `yes`: 30
- All 10 queries had at least one useful top-3 result by the lightweight expected-topic heuristic.

Topic strength:

| Query topic | Result |
| --- | --- |
| split tuning / string 6 | strong |
| pick blocking | strong |
| B+C pedals | strong |
| dominant lick on E9 | strong but noisy; many top results are overlong full-draft rows |
| harmonized scale over dominant chord | strong but noisy; overlong/full-draft rows appear high |
| 1-6-2-5 style lick | strong but noisy; high matches include broad full-draft rows |
| B-to-Bb lever | strong |
| right-hand blocking practice | strong |
| E raises in harmonized scale | strong but needs review; overlong/full-draft rows dominate |
| practice exercise using strings/frets/pedals | strong but noisy; broad combined-card row appears first |

Does curated guidance retrieve the right files for concrete teaching questions?
- Yes, the offline keyword fixture finds relevant candidate rows for all requested concrete teaching questions.
- The strongest clean-looking topics are split tuning, B+C pedals, B-to-Bb lever, and right-hand blocking.
- Some topics retrieve relevant but noisy/overlong full-draft rows, so this is not ready as a user-visible retrieval source without filtering/chunking.

Which topics look strong?
- Split tuning on string 6.
- Pick/right-hand blocking.
- B+C pedals.
- B-to-Bb/vertical lever concepts.
- Right-hand practice exercises.

Which topics look weak or noisy?
- Dominant lick queries: relevant, but overlong full-draft/source-specific solo rows dominate.
- Harmonized-scale queries: relevant, but overlong rows and instructor-phrasing flags appear high.
- 1-6-2-5 queries: relevant, but the heuristic may be overmatching number words across broad full-draft material.
- General practice exercise query: relevant, but broad combined-card material appears at the top and should be filtered or downranked.

## Required Fixes Before App Integration

Must fix or filter before app integration:
- Duplicate hash groups (`possible_duplicate_files_by_hash`).
- Under-100-word rows.
- Rows with `no_steel_specific_terms`.
- Rows with missing topic tags if topic-based routing will be used.
- Overlong rows; chunk/split before embeddings.
- Broad combined-card or quarantine-specific-card rows unless deliberately reviewed.

Should review before app integration:
- `first_person_instructor_phrasing`.
- `contains_player_should_phrase`.
- Rows with `instrument=unknown` if instrument-aware routing is expected.
- Rows with `difficulty=unknown` if lesson sequencing uses difficulty.

## Commit Safety

Safe to stage, with exact paths only:
- `scripts/ingest/build_curated_guidance_corpus.py`
- `scripts/ingest/validate_curated_guidance_corpus.py`
- `scripts/eval/eval_curated_guidance_retrieval.py`
- `docs/handoffs/task-completions/curated-guidance-inventory.md`
- `docs/handoffs/task-completions/curated-guidance-ingestion-spike.md`
- `docs/handoffs/task-completions/curated-guidance-qa-retrieval-eval.md`

Must remain uncommitted:
- `corpus-private/curated-guidance/normalized/curated-guidance-documents.jsonl`
- `corpus-private/reports/curated-guidance-inventory-full.md`
- `corpus-private/reports/curated-guidance-validation.md`
- `corpus-private/reports/curated-guidance-validation.json`
- `corpus-private/reports/curated-guidance-retrieval-eval.md`
- `corpus-private/reports/curated-guidance-retrieval-eval.json`
- any markdown guidance bodies under the local guidance source folder
- Chroma/vector stores, embeddings, private/generated reports, source-inbox raw/provenance files, corpus-v2 outputs, deployment files, design assets

Ignored-output verification:
- `.gitignore:103:corpus-private/` ignores the generated curated-guidance JSONL and reports.

## Tests And Checks

Commands run:

```bash
git status --short
git rev-parse --short HEAD
git log --oneline -5
sed -n '1,260p' scripts/ingest/build_curated_guidance_corpus.py
sed -n '1,300p' scripts/ingest/validate_curated_guidance_corpus.py
sed -n '1,220p' docs/handoffs/task-completions/curated-guidance-inventory.md
sed -n '1,260p' docs/handoffs/task-completions/curated-guidance-ingestion-spike.md
sed -n '1,240p' corpus-private/reports/curated-guidance-inventory-full.md
sed -n '1,260p' corpus-private/reports/curated-guidance-validation.md
.venv/bin/python -m py_compile scripts/ingest/build_curated_guidance_corpus.py scripts/ingest/validate_curated_guidance_corpus.py scripts/eval/eval_curated_guidance_retrieval.py
.venv/bin/python scripts/eval/eval_curated_guidance_retrieval.py
git check-ignore -v corpus-private/curated-guidance/normalized/curated-guidance-documents.jsonl corpus-private/reports/curated-guidance-retrieval-eval.md corpus-private/reports/curated-guidance-retrieval-eval.json corpus-private/reports/curated-guidance-validation.md corpus-private/reports/curated-guidance-validation.json
git diff --check
```

Results:
- `py_compile`: passed.
- Curated guidance retrieval eval: passed; evaluated 10 queries over 899 rows.
- Generated markdown report: `corpus-private/reports/curated-guidance-retrieval-eval.md`.
- Generated JSON report: `corpus-private/reports/curated-guidance-retrieval-eval.json`.
- Ignored-output verification: passed; generated `corpus-private/` files are ignored.
- `git diff --check`: passed.

Skipped:
- No pytest was run for this QA fixture because no test harness currently targets this new standalone eval script, and the requested checks were compile/eval/diff/status.

## Integration Notes

Do not blend `curated_guidance` with SGF retrieval yet.

Recommended architecture for the next slice:
- Keep `curated_guidance` as a separate retrieval layer.
- Add a pre-promotion filter for quality flags.
- Add chunking for overlong rows before embedding.
- Add a reviewed-row allowlist or quality threshold before app retrieval.
- Preserve source card labels:
  - `content_layer=curated_guidance`
  - `visibility=private_review`
- Keep private-review visibility behind auth gates.

## Risk Assessment

Risk: low for committing the scripts and handoffs.

Reason:
- Scripts are offline/local.
- Outputs are ignored.
- No Chroma, embeddings, app config, source-inbox, deployment, or SGF path was touched.

Main risk:
- If someone stages with `git add .`, private/generated reports or unrelated parked files may be accidentally swept in. Use exact-path staging only.

Rollback:
- Remove `scripts/eval/eval_curated_guidance_retrieval.py` and this handoff.
- Leave ignored `corpus-private/` artifacts unstaged or delete them only if explicitly approved.

## Commit Readiness

Safe to commit.

Only the safe-to-stage paths listed above are approved. Generated `corpus-private/` artifacts are not approved.

## Suggested Next Step

Recommended lane: 05 Backend / RAG Integration, after Repo Steward commits the ingestion/eval spike.

Exact next Lane 05 prompt:

```text
Lane 05: design a private-review curated_guidance retrieval integration plan without wiring it into production yet. Read the curated-guidance ingestion/eval handoffs and scripts. Propose a separate retrieval layer that filters duplicate, under-100-word, no-steel-term, missing-topic, and overlong rows; keeps content_layer=curated_guidance and visibility=private_review on source cards; requires auth/private-review gating; and does not blend with SGF retrieval until reviewed. Stop at plan/docs unless explicitly approved to implement.
```
