# Phase 3D Embed V2 Preflight Report

Status: `FAIL`

This report is preflight-only. It does not run embeddings and does not create or modify Chroma stores.

## Inputs

- `clean_input`: `/tmp/steel-rag-corpus-v2-review/clean_classified_chunks.refined.jsonl`
- `chunk_input`: `/tmp/steel-rag-corpus-v2-review/chunks-v2.refined.jsonl`
- `target_chroma_path`: `/Users/cory/Documents/Pocket Steel/corpus-v2/vector-stores/chroma`
- `planned_output_path`: `/Users/cory/Documents/Pocket Steel/corpus-v2/chunks-v2.jsonl`

## Summary

- Total records: `86`
- Total chunks: `152`
- Average quality score: `0.618`
- Average noise score: `0.502`
- Source metadata completeness: `152/152` (`1.0`)
- Post identity completeness: `152/152` (`1.0`)
- Contact/signature/link-only leakage: `4` (`0.026`)
- Question-only chunks: `23`
- Answer/advice chunks: `126`
- Mixed-topic quarantined chunks: `6` (`0.039`)
- Safe outside v1 paths: `True`
- Embedding commands executed: `False`

## Failures

- leakage rate 0.026 exceeds threshold 0.005

## Role Distribution
| role | count |
| --- | ---: |
| `answer_advice` | 126 |
| `question` | 23 |
| `unknown` | 3 |

## Noise Buckets
| noise bucket | count |
| --- | ---: |
| `0.00-0.20` | 4 |
| `0.21-0.40` | 53 |
| `0.41-0.60` | 48 |
| `0.61-0.80` | 46 |
| `0.81-1.00` | 1 |

## Chunk Length Distribution

- `min`: `2`
- `p50`: `219`
- `p95`: `245`
- `max`: `254`
- `avg`: `168.1`

## Top Cleanup Flags
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
| `thread_title_removed` | 1 |

## Current V1 Chroma Statement

No embeddings were run, no v2 Chroma store was created, and the current v1 Chroma store was not modified.
