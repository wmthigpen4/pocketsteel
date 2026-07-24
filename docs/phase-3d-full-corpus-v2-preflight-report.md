# Phase 3D.1 Full Corpus-V2 Preflight Report

Date: 2026-05-28

Branch: `feature/answer-api`

Status: `PASS`. Embedding still requires explicit human approval.

This was a final non-embedding cleanup and full corpus-v2 candidate regeneration. No embedding command was run, no v2 Chroma store was created, and the current v1 Chroma store was not modified.

## Scope

Input v1 chunks:

- `~/Documents/sgf-scrape-test/corpus-unified/chunks.jsonl`

Regenerated corpus-v2 outputs:

- `~/Documents/Steel Guitar RAG/corpus-v2/clean_classified_chunks.jsonl`
- `~/Documents/Steel Guitar RAG/corpus-v2/chunks-v2.jsonl`
- `~/Documents/Steel Guitar RAG/corpus-v2/reports/phase3b-full-report.md`
- `~/Documents/Steel Guitar RAG/corpus-v2/reports/phase3c-full-report.md`
- `~/Documents/Steel Guitar RAG/corpus-v2/reports/phase3d-full-preflight-report.md`
- `~/Documents/Steel Guitar RAG/corpus-v2/reports/phase3d-full-preflight.json`

Planned v2 Chroma path checked by preflight only:

- `~/Documents/Steel Guitar RAG/corpus-v2/vector-stores/chroma`

That Chroma path was not created.

## Phase 3D.1 Fixes

- Tightened punctuation-only/tiny chunk filtering so chunks with fewer than three meaningful words are skipped.
- Added residual rig-list/signature-tail trimming at chunk output time.
- Expanded gear-term detection for residual signature tails.
- Added a flagged post identity fallback for source rows that have no post UID: `source_chunk:<chunk_id>`.
- Preserved source metadata and did not alter raw v1 corpus files.

## Before/After Summary

| Metric | Before 3D.1 | After 3D.1 |
| --- | ---: | ---: |
| Input v1 rows | 401,100 | 401,100 |
| Cleaned/classified rows | 401,100 | 401,100 |
| Chunk-v2 rows | 720,383 | 717,425 |
| Answer/advice chunks | 644,295 | 641,569 |
| Question-only chunks | 30,862 | 30,872 |
| Source metadata completeness | 720,383 / 720,383 | 717,425 / 717,425 |
| Post identity completeness | 720,053 / 720,383 | 717,425 / 717,425 |
| Missing post identity chunks | 330 | 0 |
| Derived `source_chunk:` identity chunks | 0 | 329 |
| Leakage count | 3,289 | 1,395 |
| Leakage raw rate | 0.004566 | 0.001945 |
| Leakage rounded rate | 0.005 | 0.002 |
| Tiny chunks `<3` words | 2,718 | 0 |
| Punctuation/no-alphanumeric chunks | 54 | 0 |
| Average quality score | 0.667 | 0.667 |
| Average noise score | 0.418 | 0.419 |
| Mixed-topic quarantine rate | 0.000 | 0.000 |
| Full preflight | `PASS` | `PASS` |

## Post Identity Investigation

Before 3D.1, all 330 missing post-identity chunks came from:

| Source/forum | Count |
| --- | ---: |
| `sgf_phpbb_current | Pedal Steel` | 330 |

Top affected threads included:

| Thread | Missing chunks |
| --- | ---: |
| `Most Helpful Exercises For Jazz` | 37 |
| `Tall player ergonomics improvement` | 22 |
| `Guide to tuning an Emmons Push/Pull` | 21 |
| `Shortening Excel Scale Length with new neck?` | 16 |
| `Derby History` | 13 |
| `Lowering Es on E9 on Left vs. Right Knee: Current Trends` | 13 |
| `Overtuning (and Undertuning) an All-Pull Steel` | 12 |
| `Footwear` | 11 |
| `Very Early ZB Custom - Restoration` | 10 |
| `Emmons ReSound Order` | 9 |

These source rows had stable v1 `chunk_id` values and source/thread metadata, but no post UID. They are fixable for corpus-v2 provenance by using a clearly marked fallback identity, not by pretending a real post UID exists. After 3D.1, affected chunks carry `source_chunk:<chunk_id>` in `post_uids` and `post_identity_derived_from_chunk_id` in metadata normalization flags.

## Final Preflight Result

| Gate | Result |
| --- | ---: |
| Overall preflight | `PASS` |
| Total records | 401,100 |
| Total chunks | 717,425 |
| Metadata completeness | 717,425 / 717,425 (`1.000`) |
| Post identity completeness | 717,425 / 717,425 (`1.000`) |
| Contact leakage | 0 |
| Link-only leakage | 0 |
| Signature leakage | 1,395 |
| Total leakage rate | `0.002` |
| Mixed-topic quarantined chunks | 0 |
| Average quality score | 0.667 |
| Average noise score | 0.419 |
| Safe outside v1 paths | `true` |
| Embedding commands executed | `false` |

## Chunk Length Distribution

| Metric | Words |
| --- | ---: |
| Min | 3 |
| P50 | 235 |
| P95 | 245 |
| Max | 469 |
| Average | 185.9 |

## Role Distribution

| Role | Count |
| --- | ---: |
| `answer_advice` | 641,569 |
| `event` | 13,021 |
| `memorial` | 5,561 |
| `opinion` | 11,686 |
| `question` | 30,872 |
| `unknown` | 14,716 |

## Noise Buckets

| Noise bucket | Count |
| --- | ---: |
| `0.00-0.20` | 123,139 |
| `0.21-0.40` | 234,483 |
| `0.41-0.60` | 209,830 |
| `0.61-0.80` | 122,343 |
| `0.81-1.00` | 27,630 |

## Top Cleanup Flags

| Flag | Count |
| --- | ---: |
| `oversized_split` | 642,018 |
| `duplicate_sentence_removed` | 575,521 |
| `top_removed` | 532,984 |
| `raw_link_removed` | 226,410 |
| `quote_marker_detected` | 145,652 |
| `quote_heavy_flagged` | 145,652 |
| `inline_gear_signature_removed` | 114,751 |
| `contact_block_removed` | 80,976 |
| `separate_role` | 44,984 |
| `signature_removed` | 41,073 |
| `question_unpaired` | 30,872 |
| `residual_signature_tail_removed` | 20,108 |
| `gear_signature_removed` | 17,075 |
| `thread_title_removed` | 2,148 |
| `share_fragment_removed` | 145 |

## Disk Usage

| Path | Size |
| --- | ---: |
| `~/Documents/Steel Guitar RAG/corpus-v2/` | 5.8G |
| `~/Documents/Steel Guitar RAG/corpus-v2/clean_classified_chunks.jsonl` | 4.6G |
| `~/Documents/Steel Guitar RAG/corpus-v2/chunks-v2.jsonl` | 1.1G |
| `~/Documents/Steel Guitar RAG/corpus-v2/reports/phase3b-full-report.md` | 4.0K |
| `~/Documents/Steel Guitar RAG/corpus-v2/reports/phase3c-full-report.md` | 4.0K |
| `~/Documents/Steel Guitar RAG/corpus-v2/reports/phase3d-full-preflight-report.md` | 4.0K |
| `~/Documents/Steel Guitar RAG/corpus-v2/reports/phase3d-full-preflight.json` | 4.0K |

## Interpretation

Phase 3D.1 materially improved the full candidate:

- leakage dropped by 1,894 chunks
- tiny and punctuation-only chunks dropped to zero
- post identity completeness is now complete
- residual rig-list tails were trimmed in 20,108 chunks
- full preflight still passes

The remaining signature leakage count is below threshold, but it is not zero. Human review should decide whether the current residual rate is acceptable before embedding.

## Commands Run

```bash
.venv/bin/python -m pytest tests/test_phase3_clean_classify_chunks.py tests/test_phase3_chunk_v2.py tests/test_phase3_embed_v2_preflight.py
.venv/bin/python scripts/phase3_clean_classify_chunks.py --input ~/Documents/sgf-scrape-test/corpus-unified/chunks.jsonl --output corpus-v2/clean_classified_chunks.jsonl --report corpus-v2/reports/phase3b-full-report.md
.venv/bin/python scripts/phase3_chunk_v2.py --input corpus-v2/clean_classified_chunks.jsonl --output corpus-v2/chunks-v2.jsonl --report corpus-v2/reports/phase3c-full-report.md --target-words 180 --max-words 240 --min-words 8
.venv/bin/python scripts/phase3_embed_v2_preflight.py --clean-input corpus-v2/clean_classified_chunks.jsonl --chunk-input corpus-v2/chunks-v2.jsonl --target-chroma-path corpus-v2/vector-stores/chroma --planned-output-path corpus-v2/chunks-v2.jsonl --report corpus-v2/reports/phase3d-full-preflight-report.md --json-report corpus-v2/reports/phase3d-full-preflight.json
.venv/bin/python -m pytest
du -sh corpus-v2 corpus-v2/*.jsonl corpus-v2/reports/*
```

Targeted Phase 3 tests: `43 passed`.

Full test suite: `168 passed`.

## Risks

- Generated `corpus-v2/` output is large and should remain uncommitted unless explicitly approved.
- Remaining signature leakage is below threshold but not zero.
- Derived `source_chunk:` post identities are honest provenance fallbacks, but they are not true post UIDs.
- The streaming chunker assumes records for the same `thread_id` are contiguous in the cleaned input, matching the current v1 chunk ordering.

## Human Decision Needed

Yes. A human must explicitly approve any v2 embedding run.

## Recommended Next Step

Review the final Phase 3D.1 report and either approve embed-v2 generation from this candidate or request one more targeted pass to inspect the remaining 1,395 signature-leakage candidates.

## V1 Chroma Statement

No embeddings were run, no v2 Chroma store was created, and the current v1 Chroma store was not modified.
