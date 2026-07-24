# Phase 3D Embed V2 Preflight Report

Status: `PASS`

This report is preflight-only. It does not run embeddings and does not create or modify Chroma stores.

## Inputs

- `clean_input`: `/tmp/steel-rag-corpus-v2-review/clean_classified_chunks.refined.jsonl`
- `chunk_input`: `/tmp/steel-rag-corpus-v2-review/chunks-v2.refined.jsonl`
- `target_chroma_path`: `~/Documents/Steel Guitar RAG/corpus-v2/vector-stores/chroma`
- `planned_output_path`: `~/Documents/Steel Guitar RAG/corpus-v2/chunks-v2.jsonl`

## Summary

- Total records: `86`
- Total chunks: `148`
- Average quality score: `0.6`
- Average noise score: `0.545`
- Source metadata completeness: `148/148` (`1.0`)
- Post identity completeness: `148/148` (`1.0`)
- Contact/signature/link-only leakage: `0` (`0.0`)
- Question-only chunks: `22`
- Answer/advice chunks: `123`
- Mixed-topic quarantined chunks: `6` (`0.041`)
- Safe outside v1 paths: `True`
- Embedding commands executed: `False`

## Failures

- None

## Role Distribution
| role | count |
| --- | ---: |
| `answer_advice` | 123 |
| `question` | 22 |
| `unknown` | 3 |

## Noise Buckets
| noise bucket | count |
| --- | ---: |
| `0.00-0.20` | 4 |
| `0.21-0.40` | 36 |
| `0.41-0.60` | 50 |
| `0.61-0.80` | 51 |
| `0.81-1.00` | 7 |

## Chunk Length Distribution

- `min`: `2`
- `p50`: `217`
- `p95`: `243`
- `max`: `250`
- `avg`: `168.8`

## Top Cleanup Flags
| flag | count |
| --- | ---: |
| `duplicate_sentence_removed` | 144 |
| `top_removed` | 137 |
| `oversized_split` | 116 |
| `raw_link_removed` | 49 |
| `quote_heavy_flagged` | 37 |
| `quote_marker_detected` | 37 |
| `contact_block_removed` | 35 |
| `inline_gear_signature_removed` | 32 |
| `question_unpaired` | 22 |
| `mixed_topic_flagged` | 6 |
| `mixed_topic_quarantined` | 6 |
| `separate_role` | 3 |
| `gear_signature_removed` | 2 |
| `thread_title_removed` | 1 |

## Current V1 Chroma Statement

No embeddings were run, no v2 Chroma store was created, and the current v1 Chroma store was not modified.
