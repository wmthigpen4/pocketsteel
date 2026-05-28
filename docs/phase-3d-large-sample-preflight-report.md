# Phase 3D Large Sample Preflight Report

Scope: larger non-embedding Phase 3D preflight sample for corpus-v2 readiness. This run used current v1 chunks as read-only input and wrote all generated sample artifacts only under `/tmp/steel-rag-corpus-v2-large-preflight/`.

No embeddings were run. No Chroma store was created or modified.

## Sample Construction

Input source, read only:

- `/Users/cory/Documents/sgf-scrape-test/corpus-unified/chunks.jsonl`

Temporary output path:

- `/tmp/steel-rag-corpus-v2-large-preflight/`

Temporary files:

- `large_input_sample.jsonl`
- `large_input_manifest.json`
- `clean_classified_chunks.jsonl`
- `chunks-v2.jsonl`
- `phase3b-large-report.md`
- `phase3c-large-report.md`
- `phase3d-preflight-report.md`
- `phase3d-preflight.json`
- `large_preflight_analysis.json`

The sampler scanned all `401,100` current v1 rows and selected `4,400` rows using deterministic stratified sampling.

## Sample Coverage

By stratum:

| stratum | rows |
| --- | ---: |
| `forum:Electronics` | 650 |
| `forum:Pedal Steel` | 650 |
| `forum:Steel Players` | 650 |
| `forum:Steel Without Pedals` | 450 |
| `forum:Tablature` | 450 |
| `source:sgf_ubb_legacy` | 900 |
| `other` | 650 |

By forum:

| forum | rows |
| --- | ---: |
| `Steel Players` | 922 |
| `Pedal Steel` | 883 |
| `Electronics` | 838 |
| `Steel on the Web` | 528 |
| `Tablature` | 493 |
| `Steel Without Pedals` | 457 |
| `No Peddlers` | 156 |
| `Recording` | 69 |
| `Band-in-a-Box` | 19 |
| `Builders' Corner` | 19 |
| `New Product Announcements` | 13 |
| `Slide Guitar and String Bender Guitars` | 3 |

By source system:

| source system | rows |
| --- | ---: |
| `sgf_phpbb_current` | 3,500 |
| `sgf_ubb_legacy` | 900 |

## Pipeline Results

| metric | count/value |
| --- | ---: |
| Input sample rows | 4,400 |
| Cleaned/classified records | 4,400 |
| Chunk-v2 rows | 8,870 |
| Average chunk `quality_score` | 0.621 |
| Average chunk `noise_score` | 0.422 |
| Source metadata completeness | 6,820 / 8,870, 0.769 |
| Post identity completeness | 8,867 / 8,870, 1.000 |
| Leakage count | 544 |
| Leakage rate | 0.061 |
| Mixed-topic quarantined chunks | 1,093 |
| Mixed-topic quarantine rate | 0.123 |
| Answer/advice chunks | 7,975 |
| Question-only chunks | 392 |

## Preflight Status

Status: `FAIL`

Failure reasons:

- `metadata completeness 0.769 is below threshold 0.990`
- `leakage rate 0.061 exceeds threshold 0.005`
- `mixed-topic quarantine rate 0.123 exceeds threshold 0.050`

Path safety passed: planned output paths were outside v1 Chroma and outside `corpus-unified/chunks.jsonl`.

## Role Distribution

Chunk-v2 roles:

| role | count |
| --- | ---: |
| `answer_advice` | 7,975 |
| `event` | 129 |
| `memorial` | 46 |
| `opinion` | 154 |
| `question` | 392 |
| `unknown` | 174 |

## Chunk Length Distribution

| metric | words |
| --- | ---: |
| min | 1 |
| p50 | 235 |
| p95 | 245 |
| max | 374 |
| average | 185.1 |

## Noise Buckets

| noise bucket | chunks |
| --- | ---: |
| `0.00-0.20` | 1,680 |
| `0.21-0.40` | 2,510 |
| `0.41-0.60` | 2,280 |
| `0.61-0.80` | 2,143 |
| `0.81-1.00` | 257 |

## Top Cleanup Flags

| flag | count |
| --- | ---: |
| `oversized_split` | 7,778 |
| `duplicate_sentence_removed` | 6,814 |
| `top_removed` | 6,328 |
| `raw_link_removed` | 3,001 |
| `quote_heavy_flagged` | 1,616 |
| `quote_marker_detected` | 1,616 |
| `inline_gear_signature_removed` | 1,346 |
| `mixed_topic_flagged` | 1,093 |
| `mixed_topic_quarantined` | 1,093 |
| `contact_block_removed` | 934 |
| `separate_role` | 503 |
| `question_unpaired` | 392 |
| `gear_signature_removed` | 215 |
| `signature_removed` | 12 |
| `thread_title_removed` | 34 |

## Failure Analysis

### Metadata Completeness

Missing metadata count: `2,050` chunk-v2 rows.

All missing metadata rows came from `sgf_ubb_legacy`.

Reasons:

| reason | count |
| --- | ---: |
| `source_metadata_complete_false` | 2,050 |
| `missing_thread_id` | 2,050 |

By forum:

| forum | missing metadata chunks |
| --- | ---: |
| `Steel Players` | 614 |
| `Pedal Steel` | 596 |
| `Electronics` | 433 |
| `No Peddlers` | 332 |
| `Tablature` | 61 |
| `Steel Without Pedals` | 14 |

Interpretation: legacy UBB records in this sample do not carry the same scalar `thread_id` shape expected by the preflight gate. This must be resolved before embedding, either by deriving a stable legacy thread identifier or by documenting and approving a different required metadata contract for legacy rows.

### Leakage

Leakage count: `544` chunk-v2 rows.

Preflight classified all leakage as `signature`; contact and link-only leakage were `0`.

By source:

| source system | leakage chunks |
| --- | ---: |
| `sgf_phpbb_current` | 514 |
| `sgf_ubb_legacy` | 30 |

By forum:

| forum | leakage chunks |
| --- | ---: |
| `Steel Players` | 126 |
| `Tablature` | 121 |
| `Steel Without Pedals` | 102 |
| `Pedal Steel` | 88 |
| `Electronics` | 76 |
| `Steel on the Web` | 21 |
| `Recording` | 6 |
| `Builders' Corner` | 3 |
| `No Peddlers` | 1 |

Interpretation: some flagged rows are likely true signature tails, but the large sample also shows the signature-leak detector still catches gear-dense user experience and player/history content. This needs another review/tuning pass before full corpus-v2 generation is useful as an embed candidate.

### Mixed Topic Quarantine

Mixed-topic quarantined count: `1,093` chunk-v2 rows.

By source:

| source system | mixed-topic chunks |
| --- | ---: |
| `sgf_phpbb_current` | 925 |
| `sgf_ubb_legacy` | 168 |

By forum:

| forum | mixed-topic chunks |
| --- | ---: |
| `Steel Players` | 389 |
| `Pedal Steel` | 185 |
| `Steel Without Pedals` | 157 |
| `Tablature` | 116 |
| `Steel on the Web` | 101 |
| `Electronics` | 83 |
| `Recording` | 21 |
| `No Peddlers` | 19 |
| `Band-in-a-Box` | 11 |
| `Builders' Corner` | 5 |
| `Slide Guitar and String Bender Guitars` | 5 |
| `New Product Announcements` | 1 |

Interpretation: the chunker is preserving many chunks but marking them unsuitable as clean answer evidence. This is better than silently embedding them, but the rate is too high for embed-v2 readiness.

## Worst Remaining Examples

Examples are sanitized. Raw contacts and URLs are redacted in this committed report.

### High Noise: Tab Link/Contact Mix

- Thread: `The Bottle Let me down-tab for intro`
- Role: `answer_advice`
- `noise_score`: 1.0
- `quality_score`: 0.32

```text
Does anyone have tab for the intro ... Yes it's on this page> [link removed] Ricky Davis Email Ricky: [contact removed] ... Check out the 16th tab down on this page...
```

Issue: useful tab pointers are mixed with removed links/contact markers and repeated text. It should not be embedded as clean answer evidence without further chunk splitting or metadata-only link handling.

### High Noise: Chatter/Signature Mix

- Thread: `How many P/P's were ever made?`
- Role: `answer_advice`
- `noise_score`: 1.0
- `quality_score`: 0.282

```text
This thread's been hijacked ... beautiful guitar ... My rig: Infinity and Telonics ... forum banter ...
```

Issue: chatter, signatures, and some factual content are mixed. This should remain quarantined or be split more aggressively.

### High Noise: Backing Tracks Link Cluster

- Thread: `backing tracks`
- Role: `answer_advice`
- `noise_score`: 1.0
- `quality_score`: 0.35

```text
I am in Iraq ... need backing tracks ... E-mail [contact removed] ... [link removed] [link removed] [link removed] ...
```

Issue: source-card-safe after redaction, but still answer-text unsafe because the useful answer is mostly link metadata.

### Missing Metadata: Legacy Quadraverb

- Thread: `Quadraverb 2`
- Source: `sgf_ubb_legacy`
- Missing reasons: `source_metadata_complete_false`, `missing_thread_id`

```text
A friend asked me help him put some sounds in his Q2 ... programming used with the Q2 is a lot different...
```

Issue: useful content, but missing required legacy thread identity. This is a metadata contract problem, not a text cleanup problem.

### Leakage Candidate: Legacy Gear-Dense Advice

- Thread: `L-910 p.u. overloads on plucking 10th string`
- Source: `sgf_ubb_legacy`
- Missing reasons: `source_metadata_complete_false`, `missing_thread_id`

```text
I have mounted BL-910s on my Emmons P-P ... except for the volume pedal and Nashville 400s amp...
```

Issue: preflight flags as signature-like because of dense gear terms, but the excerpt reads like actual troubleshooting/user experience. This is likely a false-positive signature detector case.

### Mixed Topic: Peavey ProFex Service Thread

- Thread: `Peavey's Batteryless ProFex11 battery mod ?`
- Flags include: `mixed_topic_quarantined`

```text
Peavey UK ... battery-less mod ... service complaint ... joke/chatter reply ... explanation of whether this is a Peavey mod...
```

Issue: useful information exists, but service complaint, quote context, and chatter are mixed in one evidence chunk.

## Assessment

Large-sample preflight did not pass.

The Phase 3B/3C/3D pipeline is working as a safety gate: it preserved source metadata where present, removed raw contacts and raw links, and refused to bless an embed candidate with known remaining risks. The failures are meaningful:

- Legacy UBB needs stable `thread_id` or an approved legacy metadata contract.
- Signature-leak detection and/or cleaner rules need another pass on gear-dense user experience.
- Mixed-topic quarantine rate is too high and needs better splitting or stricter exclusion before embedding.
- Link-heavy rows should probably become metadata/review rows instead of answer evidence.

## Is Full Corpus-V2 Generation Reasonable Next?

Not as an embed candidate.

A full non-embedding corpus-v2 diagnostic may be reasonable only after addressing the legacy metadata issue and doing another leakage/mixed-topic tuning pass. Full embed-v2 should remain blocked.

## Commands Run

- `ls -lh /Users/cory/Documents/sgf-scrape-test/corpus-unified/chunks.jsonl && git branch --show-current`
- `python3 - <<'PY' ... PY` to inspect early v1 chunk ordering
- `.venv/bin/python - <<'PY' ... PY` to create `/tmp/steel-rag-corpus-v2-large-preflight/large_input_sample.jsonl`
- `.venv/bin/python scripts/phase3_clean_classify_chunks.py --input /tmp/steel-rag-corpus-v2-large-preflight/large_input_sample.jsonl --output /tmp/steel-rag-corpus-v2-large-preflight/clean_classified_chunks.jsonl --report /tmp/steel-rag-corpus-v2-large-preflight/phase3b-large-report.md`
- `.venv/bin/python scripts/phase3_chunk_v2.py --input /tmp/steel-rag-corpus-v2-large-preflight/clean_classified_chunks.jsonl --output /tmp/steel-rag-corpus-v2-large-preflight/chunks-v2.jsonl --report /tmp/steel-rag-corpus-v2-large-preflight/phase3c-large-report.md --target-words 180 --max-words 240 --min-words 8`
- `.venv/bin/python scripts/phase3_embed_v2_preflight.py --clean-input /tmp/steel-rag-corpus-v2-large-preflight/clean_classified_chunks.jsonl --chunk-input /tmp/steel-rag-corpus-v2-large-preflight/chunks-v2.jsonl --target-chroma-path /Users/cory/Documents/Pocket\\ Steel/corpus-v2/vector-stores/chroma --planned-output-path /Users/cory/Documents/Pocket\\ Steel/corpus-v2/chunks-v2.jsonl --report /tmp/steel-rag-corpus-v2-large-preflight/phase3d-preflight-report.md --json-report /tmp/steel-rag-corpus-v2-large-preflight/phase3d-preflight.json`
- `.venv/bin/python - <<'PY' ... PY` to create `/tmp/steel-rag-corpus-v2-large-preflight/large_preflight_analysis.json`

## Current V1 Chroma Statement

No embeddings were run. No embedding command was invoked. No v2 Chroma store was created. The current v1 Chroma store was not modified. `corpus-unified/chunks.jsonl` was read but not overwritten. Backend answer code, frontend code, and app configuration were not changed.
