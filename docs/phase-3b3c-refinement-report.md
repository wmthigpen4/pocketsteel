# Phase 3B/3C Refinement Report

Scope: refine the sample-safe Phase 3B cleaner/classifier and Phase 3C chunker-v2 before any embed-v2 approval. This work does not modify v1 Chroma, run embeddings, delete corpus files, run live SGF scraping, overwrite production chunks, change backend code, change frontend code, or switch app configuration.

## What Changed

- Refined `sale_wanted` classification so useful technical advice with price, buying, or eBay language is not automatically classified as classifieds content.
- Refined `contact_block` handling so contact details are removed and flagged, while useful advice can remain `answer_advice`.
- Tightened event classification so broad words like `show` do not dominate quote-heavy or advice-heavy chunks unless event terms dominate.
- Added inline gear-signature removal for flattened rig-list tails in answer/advice records.
- Made chunker-v2 quarantine mixed-topic answer chunks more aggressively by adding `mixed_topic_quarantined`, raising `noise_score`, and capping `quality_score`.
- Narrowed mixed-topic quarantine so already-removed contact/signature artifacts do not automatically quarantine otherwise useful answer chunks.
- Added regression tests for the above cases.

## Refined Sample Counts

Temporary review output path:

- `/tmp/steel-rag-corpus-v2-review/`

Refined output files:

- `/tmp/steel-rag-corpus-v2-review/clean_classified_chunks.refined.jsonl`
- `/tmp/steel-rag-corpus-v2-review/chunks-v2.refined.jsonl`
- `/tmp/steel-rag-corpus-v2-review/review_stats.refined.json`

| metric | count/value |
| --- | ---: |
| Input sample count | 86 |
| Cleaned/classified output count | 86 |
| Chunk-v2 output count | 152 |
| Excluded source record count | 5 |
| Cleaned average `noise_score` | 0.494 |
| Cleaned average `quality_score` | 0.585 |
| Chunk-v2 average `noise_score` | 0.502 |
| Chunk-v2 average `quality_score` | 0.618 |
| Cleaned metadata completeness | 100.0% |
| Cleaned post identity completeness | 100.0% |
| Chunk metadata completeness | 100.0% |
| Chunk post identity completeness | 100.0% |

Compared with the previous sample review, the refined classifier preserves many mixed advice rows instead of excluding them wholesale. The higher chunk count is mostly from preserving and splitting useful advice records that were previously excluded as `contact_block`, `sale_wanted`, or `event`.

## Role Distribution

Cleaned/classified records:

| role | count |
| --- | ---: |
| `answer_advice` | 56 |
| `contact_block` | 1 |
| `gear_signature` | 1 |
| `link_only` | 2 |
| `question` | 23 |
| `sale_wanted` | 1 |
| `unknown` | 2 |

Chunk-v2 outputs:

| role | count |
| --- | ---: |
| `answer_advice` | 126 |
| `question` | 23 |
| `unknown` | 3 |

Excluded source records:

| role | excluded |
| --- | ---: |
| `contact_block` | 1 |
| `gear_signature` | 1 |
| `link_only` | 2 |
| `sale_wanted` | 1 |

## Cleanup Flags

Top cleaner/classifier flags:

| flag | count |
| --- | ---: |
| `duplicate_sentence_removed` | 81 |
| `top_removed` | 76 |
| `contact_block_removed` | 18 |
| `quote_marker_detected` | 16 |
| `inline_gear_signature_removed` | 9 |
| `gear_signature_removed` | 2 |
| `thread_title_removed` | 1 |

Top chunk-v2 flags:

| flag | count |
| --- | ---: |
| `duplicate_sentence_removed` | 148 |
| `top_removed` | 140 |
| `oversized_split` | 119 |
| `quote_heavy_flagged` | 37 |
| `quote_marker_detected` | 37 |
| `contact_block_removed` | 36 |
| `question_unpaired` | 23 |
| `inline_gear_signature_removed` | 18 |
| `mixed_topic_flagged` | 6 |
| `mixed_topic_quarantined` | 6 |
| `separate_role` | 3 |
| `gear_signature_removed` | 2 |

## Before And After Examples

Examples are sanitized for this committed report. The temporary `/tmp` review pack contains local derived excerpts for detailed inspection.

### Advice With Price/eBay Language

- Source: `Need some wah wah advice.`
- Refined role: `answer_advice`
- Flags: `duplicate_sentence_removed`, `top_removed`

Before:

```text
I was checking out my three old wah pedals ... I have seen some 100K, 470K and 500K pots listed on the net for up to $30 ... Top ...
```

After:

```text
I was checking out my three old wah pedals ... Everything I've seen indicates a Dunlop wah has always used a 100K pot ...
```

Result: buying/price language no longer forces `sale_wanted` when the row contains substantive technical advice.

### Contact Details Removed, Advice Preserved

- Source: `Crate Power Block Amp = Zero Point Energy Source???`
- Refined role: `answer_advice`
- Flags: `contact_block_removed`, `duplicate_sentence_removed`, `top_removed`

Before:

```text
I used mine New Years Eve, with a POD XT ... [raw contact redacted] ... Top ...
```

After:

```text
I used mine New Years Eve, with a POD XT ... It held its own and was a lot lighter than my rack preamp/effects processor/power amp ...
```

Result: contact artifacts are removed, but useful user-experience content is no longer excluded wholesale.

### Inline Gear Signature Removed

- Source: `Vegas 400 reverb problem`
- Refined role: `answer_advice`
- Flags: `duplicate_sentence_removed`, `inline_gear_signature_removed`, `top_removed`

Before:

```text
I got my old Vegas back ... Any ideas? I would like to get this cool amp back in action. Dave Zirbel- Sierra S-10 ... Top ...
```

After:

```text
I got my old Vegas back ... the reverb does not work ... Any ideas? I would like to get this cool amp back in action ...
```

Result: flattened rig-list tails are moved out of answer text when they look like signatures.

### Quote-Heavy Advice Not Mislabeled As Event

- Source: `Why does my Peavy sound so bad ?`
- Refined role: `answer_advice`
- Flags: `duplicate_sentence_removed`, `quote_marker_detected`, `top_removed`

Before:

```text
... wrote: ... I've been doodling with Terry Downs' Blue Tele Demo ... Top ...
```

After:

```text
... I've been doodling with Terry Downs' Blue Tele Demo ... I have always had a problem with my Peaveys ...
```

Result: broad event-like words no longer dominate quote-heavy/advice-heavy rows unless event terms are the main content.

### Question Not Promoted To Advice

- Source: `QA issues`
- Refined role: `question`
- Flags: `duplicate_sentence_removed`, `top_removed`

Before:

```text
Were they ever fixed by Fender? Top ... Sorry, this should have been with the "amp of my dreams" post. Top ...
```

After:

```text
Were they ever fixed by Fender? Sorry, this should have been with the "amp of my dreams" post.
```

Result: the row remains `question`, not `answer_advice`.

### Mixed Topic Quarantined

- Source: `Peavey's Batteryless ProFex11 battery mod ?`
- Chunk-v2 role: `answer_advice`
- Flags include: `mixed_topic_flagged`, `mixed_topic_quarantined`, `oversized_split`
- Refined chunk `noise_score`: `0.713`
- Refined chunk `quality_score`: `0.350`

Excerpt:

```text
This is no reflection on Mike Brown or Ken Fox ... I sent one of mine to Peavey UK with a problem of low output ...
```

Result: mixed-topic content can still be retained for review, but chunker-v2 now marks it low quality instead of allowing it to look like a clean answer chunk.

## Tests

Targeted command:

```bash
.venv/bin/python -m pytest tests/test_phase3_clean_classify_chunks.py tests/test_phase3_chunk_v2.py
```

Result: `24 passed`.

Full command:

```bash
.venv/bin/python -m pytest
```

Result: `129 passed`.

## Assessment

The refinements improve the main sample-review failures. Useful advice is less likely to be discarded merely because it contains price, buying, contact, or inline signature artifacts. Chunker-v2 now treats real mixed-topic answer chunks as lower-quality/quarantined evidence.

Embed-v2 should still remain blocked. The refined sample is better, but the next step should be a non-embedding Phase 3D preflight/audit that measures these heuristics across a larger corpus-v2 candidate and reports threshold decisions before any vector store is created.

## Commands Run

- `.venv/bin/python -m pytest tests/test_phase3_clean_classify_chunks.py tests/test_phase3_chunk_v2.py`
- `.venv/bin/python scripts/phase3_clean_classify_chunks.py --input /tmp/steel-rag-corpus-v2-review/representative_input_sample.jsonl --output /tmp/steel-rag-corpus-v2-review/clean_classified_chunks.refined.jsonl --report /tmp/steel-rag-corpus-v2-review/phase3b-refined-sample-report.md`
- `.venv/bin/python scripts/phase3_chunk_v2.py --input /tmp/steel-rag-corpus-v2-review/clean_classified_chunks.refined.jsonl --output /tmp/steel-rag-corpus-v2-review/chunks-v2.refined.jsonl --report /tmp/steel-rag-corpus-v2-review/phase3c-refined-sample-report.md --target-words 180 --max-words 240 --min-words 8`
- `.venv/bin/python - <<'PY' ... PY` to write `/tmp/steel-rag-corpus-v2-review/review_stats.refined.json`
- `.venv/bin/python -m pytest`

## Current V1 Chroma Statement

The current v1 Chroma store was not modified. This refinement did not reset Chroma, run embeddings, delete corpus files, run live SGF scraping, overwrite `corpus-unified/chunks.jsonl`, change backend answer code, change frontend code, or switch app config.
