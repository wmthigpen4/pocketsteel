# Phase 3D Full Corpus-V2 Preflight Report

Date: 2026-05-28

Branch: `feature/answer-api`

Status: `PASS`, with human-review cautions before embedding approval.

This was a non-embedding full corpus-v2 candidate generation and preflight run. No embedding command was run, no v2 Chroma store was created, and the current v1 Chroma store was not modified.

## Scope

Input v1 chunks:

- `/Users/cory/Documents/sgf-scrape-test/corpus-unified/chunks.jsonl`

Generated corpus-v2 candidate outputs:

- `/Users/cory/Documents/Pocket Steel/corpus-v2/clean_classified_chunks.jsonl`
- `/Users/cory/Documents/Pocket Steel/corpus-v2/chunks-v2.jsonl`
- `/Users/cory/Documents/Pocket Steel/corpus-v2/reports/phase3b-full-report.md`
- `/Users/cory/Documents/Pocket Steel/corpus-v2/reports/phase3c-full-report.md`
- `/Users/cory/Documents/Pocket Steel/corpus-v2/reports/phase3d-full-preflight-report.md`
- `/Users/cory/Documents/Pocket Steel/corpus-v2/reports/phase3d-full-preflight.json`

Planned v2 Chroma path checked by preflight only:

- `/Users/cory/Documents/Pocket Steel/corpus-v2/vector-stores/chroma`

That Chroma path was not created.

## Path Safety

- `corpus-v2/` is outside `/Users/cory/Documents/sgf-scrape-test/corpus-unified/`.
- `corpus-v2/chunks-v2.jsonl` does not overwrite `/Users/cory/Documents/sgf-scrape-test/corpus-unified/chunks.jsonl`.
- `corpus-v2/vector-stores/chroma` is outside the v1 Chroma path.
- `corpus-v2/vector-stores/chroma` did not exist after the run.

## Counts

| Metric | Value |
| --- | ---: |
| Input v1 rows | 401,100 |
| Cleaned/classified rows | 401,100 |
| Chunk-v2 rows | 720,383 |
| Answer/advice chunks | 644,295 |
| Question-only chunks | 30,862 |
| Mixed-topic quarantined chunks | 0 |

The chunk-v2 count is higher than the v1 row count because many oversized answer/advice records split into retrieval-sized pieces.

## Preflight Result

| Gate | Result |
| --- | ---: |
| Overall preflight | `PASS` |
| Metadata completeness | 720,383 / 720,383 (`1.000`) |
| Post identity completeness | 720,053 / 720,383 (`1.000` rounded, 330 missing) |
| Leakage count | 3,289 |
| Leakage rate | 0.004566 raw (`0.005` rounded) |
| Mixed-topic quarantine rate | 0.000 |
| Average quality score | 0.667 |
| Average noise score | 0.418 |
| Embedding commands executed | `false` |

The leakage gate passed because 3,289 / 720,383 is below the 0.005 threshold, even though the rounded display is `0.005`.

## Chunk Length Distribution

| Metric | Words |
| --- | ---: |
| Min | 0 |
| P50 | 236 |
| P95 | 245 |
| Max | 469 |
| Average | 186.2 |

Human-review caution: some punctuation-only chunks still exist after oversized splitting. These are not numerous enough to fail current preflight, but they are not useful embedding candidates.

## Role Distribution

| Role | Count |
| --- | ---: |
| `answer_advice` | 644,295 |
| `event` | 13,084 |
| `memorial` | 5,584 |
| `opinion` | 11,760 |
| `question` | 30,862 |
| `unknown` | 14,798 |

## Noise Buckets

| Noise bucket | Count |
| --- | ---: |
| `0.00-0.20` | 123,601 |
| `0.21-0.40` | 235,760 |
| `0.41-0.60` | 211,071 |
| `0.61-0.80` | 122,680 |
| `0.81-1.00` | 27,271 |

## Top Cleanup Flags

| Flag | Count |
| --- | ---: |
| `oversized_split` | 644,987 |
| `duplicate_sentence_removed` | 577,984 |
| `top_removed` | 535,292 |
| `raw_link_removed` | 227,371 |
| `quote_marker_detected` | 146,259 |
| `quote_heavy_flagged` | 146,259 |
| `inline_gear_signature_removed` | 113,749 |
| `contact_block_removed` | 81,319 |
| `separate_role` | 45,226 |
| `signature_removed` | 41,246 |
| `question_unpaired` | 30,862 |
| `gear_signature_removed` | 17,019 |
| `thread_title_removed` | 2,168 |
| `share_fragment_removed` | 146 |
| `navigation_removed` | 105 |

## Disk Usage

| Path | Size |
| --- | ---: |
| `/Users/cory/Documents/Pocket Steel/corpus-v2/` | 5.8G |
| `/Users/cory/Documents/Pocket Steel/corpus-v2/clean_classified_chunks.jsonl` | 4.6G |
| `/Users/cory/Documents/Pocket Steel/corpus-v2/chunks-v2.jsonl` | 1.1G |
| `/Users/cory/Documents/Pocket Steel/corpus-v2/reports/phase3b-full-report.md` | 4.0K |
| `/Users/cory/Documents/Pocket Steel/corpus-v2/reports/phase3c-full-report.md` | 4.0K |
| `/Users/cory/Documents/Pocket Steel/corpus-v2/reports/phase3d-full-preflight-report.md` | 4.0K |
| `/Users/cory/Documents/Pocket Steel/corpus-v2/reports/phase3d-full-preflight.json` | 4.0K |

## Worst Remaining Examples

Representative examples are sanitized where needed.

### Residual Signature Leakage

- `Small mixer, too much noise`: useful troubleshooting text remains, but a gear/name tail still trips signature detection. This is answer-text-unsafe if the tail is included in an embedded chunk.
- `Nashville 1000 or the 112 ??`: advice about mixer/headphone/direct-line use is followed by a rig list tail. The chunk is mostly useful, but should be trimmed before final embedding.
- `Rack set up or Combo amp.`: useful rack workflow advice is followed by a gear inventory tail. This is the main remaining leakage pattern.

### Highest Noise

- `George L cable assembly question`: quote-heavy vendor/contact discussion, contact markers removed, but the chunk still combines question, quoted vendor language, and advice.
- `new peavey steel amp`: quote-heavy product speculation and show chatter. It is source-faithful but weak as direct answer evidence.
- `Need source for MIDI jacks - Please Close`: question plus contact/link replacement markers and signature remnants. It should remain low-ranked or be excluded from answer evidence.

### Lowest Quality

- Several lowest-quality chunks are question-first threads with answers embedded later in the same split. They are marked as `question`, `question_unpaired`, or high-noise. This is tolerable if retrieval ranking does not promote them as advice.

### Punctuation-Only/Tiny Chunks

Examples include chunks whose `chunk_text` is `. . .`, `-`, `.`, `...`, or `!`. These are artifacts of oversized splitting after cleanup. They did not fail current preflight, but they are not safe to embed as useful retrieval evidence.

### Missing Post Identity

Preflight found 330 chunks without post identity, all above the threshold tolerance. Representative examples are from `Pedal Steel` thread `Derby History`, where the chunk has complete source metadata but no `post_uids`. These are source-card-safe enough for thread-level provenance, but weaker for post-level citation.

## Interpretation

The full corpus-v2 candidate passes the current Phase 3D gates:

- metadata completeness is complete
- post identity completeness is above threshold
- leakage is just under threshold
- mixed-topic quarantine is not above threshold
- v2 paths are safely outside v1 paths

However, embedding should remain blocked until a human explicitly approves proceeding. The main human-review concerns are:

- residual signature tails are still present in 3,289 chunks
- punctuation-only chunks should ideally be skipped before final embedding
- some quote-heavy chunks remain technically valid but weak as answer evidence
- 330 chunks lack post identity and rely on thread/source metadata

## Commands Run

```bash
.venv/bin/python -m pytest tests/test_phase3_clean_classify_chunks.py tests/test_phase3_chunk_v2.py tests/test_phase3_embed_v2_preflight.py
mkdir -p corpus-v2/reports
.venv/bin/python scripts/phase3_clean_classify_chunks.py --input /Users/cory/Documents/sgf-scrape-test/corpus-unified/chunks.jsonl --output corpus-v2/clean_classified_chunks.jsonl --report corpus-v2/reports/phase3b-full-report.md
.venv/bin/python scripts/phase3_chunk_v2.py --input corpus-v2/clean_classified_chunks.jsonl --output corpus-v2/chunks-v2.jsonl --report corpus-v2/reports/phase3c-full-report.md --target-words 180 --max-words 240 --min-words 8
.venv/bin/python scripts/phase3_embed_v2_preflight.py --clean-input corpus-v2/clean_classified_chunks.jsonl --chunk-input corpus-v2/chunks-v2.jsonl --target-chroma-path corpus-v2/vector-stores/chroma --planned-output-path corpus-v2/chunks-v2.jsonl --report corpus-v2/reports/phase3d-full-preflight-report.md --json-report corpus-v2/reports/phase3d-full-preflight.json
du -sh corpus-v2 corpus-v2/*.jsonl corpus-v2/reports/*
```

Full test suite result: `150 passed`.

## Risks

- Generated `corpus-v2/` output is large and should remain uncommitted unless explicitly approved.
- Residual signature leakage is below threshold but still close enough to deserve review.
- Current preflight does not fail punctuation-only chunks.
- The streaming chunker assumes records for the same `thread_id` are contiguous in the cleaned input, matching the current v1 chunk ordering.

## Human Decision Needed

Yes. A human must explicitly approve any embedding run. Recommended decision before embedding: either approve a small Phase 3D.1 cleanup pass for residual signature/tiny chunk filtering, or accept the current preflight pass and approve embed-v2 generation.

## Recommended Next Step

Run a small Phase 3D.1 refinement that skips punctuation-only chunks and trims residual rig-list tails from answer chunks, then regenerate corpus-v2 and rerun preflight before embedding approval.

## V1 Chroma Statement

No embeddings were run, no v2 Chroma store was created, and the current v1 Chroma store was not modified.
