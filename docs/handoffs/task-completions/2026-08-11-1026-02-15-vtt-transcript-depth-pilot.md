# VTT Transcript Depth Pilot

## Task Summary

Lanes: `02 Corpus Pipeline` and `15 QA / Answer Eval`

Mode: read-only/private-corpus analysis plus an ignored offline retrieval experiment.

Requested:

- Determine whether the existing `vtt-test` summaries simplified steel-guitar instruction too aggressively.
- Test whether transcript-derived detail can enhance the Steel Guitar Brain without reintroducing personally identifiable information.

Completed:

- Inspected the current curated-guidance ingestion, validation, retrieval, and protected-routing code.
- Paired 297 transcript records with compact summary records without changing any raw source.
- Quantified depth and known privacy-marker changes across raw transcript text, privacy-cleaned full guidance, and compact summaries.
- Built an ignored, offline overview-plus-detail retrieval pilot from the cleanest structured-lesson cohort.
- Compared compact-summary retrieval with technical-detail and hybrid retrieval.
- Re-ran the existing curated-guidance build, validation, and ten-query offline eval.

Intentionally not completed:

- No raw transcript, cleaned transcript, guidance markdown, or source metadata was modified.
- No embeddings or vector indexes were built.
- No SGF corpus, scraper, retrieval ranking, answer prompt, answer synthesis, source card, API response, UI, auth, deployment, or protected-preview behavior was changed.
- No private body text, lesson titles, filenames, or requester/member metadata is included in this handoff.

## Current State Finding

The VTT material does not currently enhance answer text.

- The `curated_guidance` retriever is default-off and admin/backstage gated.
- `/api/answer` can call it and record only status and result count.
- Retrieved curated-guidance excerpts are not passed into answer synthesis and are not returned in source cards or the public response.

The existing normalized corpus is also not a safe promotion unit:

- It recursively ingests all 899 markdown files beneath `guidance-cleaned`, not an approved source manifest.
- The 899 rows include 303 full drafts, 580 compact/derived summary drafts, six samples, five prototypes, three specifications, and two corpus-level confirmation documents.
- The current local filter considers 617 rows retrievable.
- Those 617 include 285 summary rows derived from private/quarantined meeting groups.
- The normalized schema does not carry the original record's `candidate_status`, `corpus_class`, `privacy_action`, `licensing_action`, `allowed_for_embedding`, or `dry_run_only` decisions.
- All 303 full-draft source records remain `allowed_for_embedding=false` and `dry_run_only=true`.

This does not create a current answer leak because curated guidance is not composed into answers, but it means the 899-row corpus must not be wired into answer synthesis as-is.

## Summary Depth Finding

The compact summaries are useful overviews, but they are too compressed to be the only instructional evidence layer.

For the 62 paired structured-lesson records in the cleanest existing cohort:

- Privacy-cleaned full guidance: 109,623 words.
- Compact summaries: 20,351 words.
- Compact-summary word retention: 18.6%.
- Compact-summary exact source-anchor recall: 43.2%.
- Compact-summary anchor-mention retention: 62.1%.
- Lessons missing at least two source-specific technical anchors in the compact summary: 50/62.

Technical anchors in this analysis include concrete strings, frets, pedals, levers, grips, progressions, and named steel techniques. Exact source-anchor recall measures whether the same source-specific anchor survived; it does not give credit for a new generic example added by the summary.

The summaries often retain the concept and add a clean practice example, which is valuable. The loss is mainly in alternate positions, motion sequences, pedal/lever transitions, exceptions, troubleshooting cues, and repeated procedural detail.

## Privacy Finding

The earlier cleanup materially reduced known identity/logistics residue.

For the 62 structured records used in the pilot:

- Known marker hits in privacy-cleaned full guidance: 0.
- Known marker hits in compact summaries: 0.
- Hits from an additional local scan for contact data, course/platform logistics, presenter/member terms, phone-like patterns, and a small set of personal-life phrases: 0.

This is evidence that the cleanup worked for known patterns, not proof that the text is free of all PII, indirect identifiers, personal anecdotes, or rights issues. No person-name NER review or human line review was performed in this task.

The other cohorts remain blocked:

- The 95 review-required full-guidance records retain 40 known risk-marker hits in aggregate.
- The 140 quarantined/private-meeting sources remain excluded regardless of whether a derived summary passes a simple marker scan.

## Offline Technical-Detail Pilot

The pilot used only paired structured records whose existing guidance scan and stricter local scan were both zero.

It created:

- 62 compact overview rows.
- 521 technical-detail chunks across 57 lessons.
- Five paired lessons had no technical anchors under the pilot detector.
- 43 source-held detail-recovery query probes.

The detail chunks were extractive for measurement, private, ignored by git, marked `answer_quote_allowed=false`, and never embedded or sent to answer generation.

Content retention:

- Technical-detail words: 17,399, or 15.9% of the privacy-cleaned full guidance.
- Exact source-anchor recall: 97.1%.
- Anchor-mention retention: 96.2%.

The compact summaries and technical spans therefore use a similar word budget, but the technical spans retain substantially more source-specific mechanics. They are not a replacement for overviews; they are a complementary detail layer.

## Retrieval Result

The 43 detail-recovery probes were constructed from technical anchors present in each source's privacy-cleaned full guidance but absent from its compact summary. Results were collapsed by source ID.

| Corpus | Top 1 | Top 3 | Top 5 | MRR |
| --- | ---: | ---: | ---: | ---: |
| Compact summary only | 4/43 | 7/43 | 8/43 | 0.166 |
| Technical detail only | 6/43 | 15/43 | 23/43 | 0.311 |
| Overview + technical detail | 8/43 | 14/43 | 19/43 | 0.313 |

The hybrid nearly doubled mean reciprocal rank and doubled Top-3 recovery versus compact summaries alone. Absolute performance is still too low for release because the current scorer is a small local lexical fixture, not the intended final retriever.

On the existing ten broad teaching queries:

- Summary-only: 10/10 had a useful Top-3 result.
- Detail-only: 10/10 had a useful Top-3 result.
- Hybrid: 10/10 had a useful Top-3 result.

The extra detail improved source-specific recovery without weakening the existing broad-topic fixture.

## Product And Corpus Decision

The VTT material should enhance the Steel Guitar Brain, but it should not be merged into or labeled as SGF content.

Recommended model:

1. Keep SGF evidence as the public, attributable forum layer.
2. Keep VTT-derived instruction as a distinct private curated-teaching layer.
3. Retain one compact overview per approved lesson.
4. Add small, paraphrased atomic teaching cards for setup, procedure, alternate positions, common mistakes, and transfer.
5. Carry source-level privacy, licensing, embedding, and quote decisions onto every card.
6. Set `answer_quote_allowed=false` by default; answer with paraphrase, not transcript excerpts.
7. Validate strings, frets, pedals, levers, notes, and chord functions against deterministic copedent logic before a card can influence an answer.
8. Retrieve overview and detail separately, then collapse/group results by source so one long lesson cannot flood context.

Do not use the pilot's extractive chunks as production answer context. They establish that the detail is valuable. The production artifact should be a paraphrased, reviewed atomic card with explicit technical fields and provenance.

## Recommended Next Slice

Build a v2 private-review corpus generator for the 62 structured records only, without embeddings or runtime wiring.

Required behavior:

- Read an explicit approved manifest; do not recursively ingest all `guidance-cleaned` markdown.
- Preserve parent overview and child-card relationships.
- Produce paraphrased atomic cards with `concept`, `setup`, `procedure`, `technical_anchors`, `common_mistakes`, and `transfer` fields.
- Preserve `source_id`, source hash, corpus class, privacy action, licensing action, approval state, and quote policy.
- Exclude all review-required and quarantined/private-meeting records.
- Run PII/identity, licensing, ASR, and deterministic music-validity review queues.
- Evaluate on the 43 detail probes plus a human-authored question/answer-completeness set.
- Stop at a private review report. Do not embed or change `/api/answer` until the corpus and eval are explicitly approved.

## Files Changed

Created tracked handoff:

- `docs/handoffs/task-completions/2026-08-11-1026-02-15-vtt-transcript-depth-pilot.md`

Generated ignored/private artifacts:

- `corpus-private/curated-guidance/normalized/curated-guidance-documents.jsonl`
- `corpus-private/curated-guidance/experiments/vtt-technical-detail-pilot.jsonl`
- `corpus-private/reports/curated-guidance-inventory-full.md`
- `corpus-private/reports/curated-guidance-validation.md`
- `corpus-private/reports/curated-guidance-validation.json`
- `corpus-private/reports/curated-guidance-retrieval-eval.md`
- `corpus-private/reports/curated-guidance-retrieval-eval.json`
- `corpus-private/reports/vtt-technical-detail-pilot.md`
- `corpus-private/reports/vtt-technical-detail-pilot.json`

Modified source files: none.

Deleted files: none.

## Tests And Checks

Commands run:

```bash
.venv/bin/python scripts/ingest/build_curated_guidance_corpus.py
.venv/bin/python scripts/ingest/validate_curated_guidance_corpus.py
.venv/bin/python scripts/eval/eval_curated_guidance_retrieval.py
.venv/bin/python -m pytest tests/test_curated_guidance_retriever.py -q
.venv/bin/python -m py_compile scripts/ingest/build_curated_guidance_corpus.py scripts/ingest/validate_curated_guidance_corpus.py scripts/eval/eval_curated_guidance_retrieval.py steel_guitar_rag/curated_guidance_retriever.py
git check-ignore -v corpus-private/curated-guidance/normalized/curated-guidance-documents.jsonl corpus-private/curated-guidance/experiments/vtt-technical-detail-pilot.jsonl corpus-private/reports/vtt-technical-detail-pilot.json corpus-private/reports/vtt-technical-detail-pilot.md
```

Results:

- Curated-guidance build: 899 rows processed, 0 skipped.
- Validation: 899 rows, 0 structural failures, 972 warnings.
- Existing offline retrieval fixture: ten queries completed over 899 rows.
- Focused retriever tests: 6 passed.
- Python compile checks: passed.
- All checked private/generated outputs are ignored by `.gitignore`.

## Integration Notes

- The current recursive 899-row builder should be treated as an inventory spike, not the input contract for answer generation.
- Current `curated_guidance` API routing proves only fail-closed retrieval invocation. It does not prove answer quality or source-safe composition.
- Any future answer integration must preserve the distinction between forum evidence and curated lesson instruction.
- Any future embedding run remains a separate RED approval and is not authorized by this pilot.

## Risk Assessment

Risk: medium for a future implementation; low for this completed offline pilot.

Why:

- The pilot generated only ignored private artifacts and changed no runtime behavior.
- Source-specific technical value is clear, but automated scans are not a substitute for human privacy/licensing review.
- Extractive transcript-derived spans carry verbatim/copyright risk and must not become answer context.
- The current normalized corpus loses source approval states and includes quarantine-derived rows that a later synthesis path could misuse.

Rollback:

- Remove the ignored pilot outputs if they are no longer useful. No code, runtime, vector store, or source rollback is required.

## Human Decision Needed

Yes, before the next corpus implementation slice:

- Approve the 62 clean structured records as the only v2 pilot cohort.
- Confirm that the next slice remains private-review/admin-only, quote-disabled, unembedded, and stops at review/evaluation.

A separate explicit decision is still required before embeddings, answer synthesis, source-card exposure, protected-preview enablement, or broader cohorts.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-08-11-1026-02-15-vtt-transcript-depth-pilot.md`

## Files That Must Not Be Staged

- `corpus-private/`
- Any file beneath `~/Documents/vtt-test/`
- Raw transcripts, VTT/WebVTT segments, cleaned transcripts, private summaries, or derived lesson bodies
- Chroma/vector stores or embeddings
- SGF scrape/corpus outputs
- The unrelated pre-existing untracked handoff `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md`

## Recommended Next Lane

Recommended lane: `02 Corpus Pipeline`, followed by independent `15 QA / Answer Eval` review.

Suggested next task:

```text
Lane 02: Using the approved 62 structured vtt-test records only, implement a v2 private-review overview-plus-atomic-card corpus generator from the privacy-cleaned full guidance. Preserve all source approval/privacy/licensing fields, paraphrase rather than copy source sentences, validate technical anchors, keep answer quoting disabled, exclude review-required and quarantined sources, write only ignored corpus-private outputs, run the detail and broad-topic evals, and stop before embeddings or runtime wiring.
```

## Commit Readiness

Safe to commit for the tracked handoff only. No implementation or private/generated artifact is ready to commit.
