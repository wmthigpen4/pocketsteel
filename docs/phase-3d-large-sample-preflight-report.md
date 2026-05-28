# Phase 3D Large Sample Preflight Rerun

Scope: fix and rerun the larger non-embedding Phase 3D preflight sample for corpus-v2 readiness. This run used current v1 chunks as read-only input and wrote all generated sample artifacts only under `/tmp/steel-rag-corpus-v2-large-preflight/`.

No embeddings were run. No Chroma store was created or modified.

## Fixes Applied

- Derived stable scalar `thread_id` values for `sgf_ubb_legacy` rows from `legacy_thread_uid` or legacy thread URLs.
- Preserved `source_system=sgf_ubb_legacy` while marking rows with `metadata_normalization_flags=["legacy_thread_id_derived"]`.
- Stopped promoting answer records with unresolved low-value mixed roles into chunk-v2 answer evidence.
- Removed inline dashed signature spans before the next author/date boundary when they look like signatures.
- Tightened preflight signature leakage detection so tab underlines and gear-dense troubleshooting are not overcounted as signatures.

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
- `large_preflight_analysis_after_fixes.json`

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

By source system:

| source system | rows |
| --- | ---: |
| `sgf_phpbb_current` | 3,500 |
| `sgf_ubb_legacy` | 900 |

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

## Before/After Counts

| metric | before fixes | after fixes |
| --- | ---: | ---: |
| Input sample rows | 4,400 | 4,400 |
| Cleaned/classified records | 4,400 | 4,400 |
| Chunk-v2 rows | 8,870 | 7,704 |
| Average chunk `quality_score` | 0.621 | 0.676 |
| Average chunk `noise_score` | 0.422 | 0.394 |
| Source metadata completeness | 0.769 | 1.000 |
| Post identity completeness | 1.000 | 1.000 |
| Leakage count | 544 | 38 |
| Leakage rate | 0.061 | 0.005 |
| Mixed-topic quarantined chunks | 1,093 | 0 |
| Mixed-topic quarantine rate | 0.123 | 0.000 |
| Answer/advice chunks | 7,975 | 6,839 |
| Question-only chunks | 392 | 400 |

The reduced chunk count is expected: mixed-topic rows are no longer emitted as answer evidence, and more signature/footer text is removed before chunking.

## Preflight Status

Status: `PASS`

Failure reasons: none.

Path safety passed: planned output paths were outside v1 Chroma and outside `corpus-unified/chunks.jsonl`.

Important caution: this is a sample preflight pass, not approval to run embeddings.

## Role Distribution

Chunk-v2 roles after fixes:

| role | count |
| --- | ---: |
| `answer_advice` | 6,839 |
| `event` | 126 |
| `memorial` | 46 |
| `opinion` | 137 |
| `question` | 400 |
| `unknown` | 156 |

## Chunk Length Distribution

| metric | words |
| --- | ---: |
| min | 1 |
| p50 | 235 |
| p95 | 245 |
| max | 374 |
| average | 185.0 |

## Noise Buckets

| noise bucket | chunks |
| --- | ---: |
| `0.00-0.20` | 1,666 |
| `0.21-0.40` | 2,407 |
| `0.41-0.60` | 2,196 |
| `0.61-0.80` | 1,192 |
| `0.81-1.00` | 243 |

## Top Cleanup Flags

| flag | count |
| --- | ---: |
| `oversized_split` | 6,739 |
| `duplicate_sentence_removed` | 5,814 |
| `top_removed` | 5,378 |
| `raw_link_removed` | 2,547 |
| `quote_heavy_flagged` | 1,394 |
| `quote_marker_detected` | 1,394 |
| `inline_gear_signature_removed` | 1,107 |
| `contact_block_removed` | 781 |
| `separate_role` | 465 |
| `question_unpaired` | 400 |
| `signature_removed` | 380 |
| `gear_signature_removed` | 200 |
| `thread_title_removed` | 27 |

## Remaining Examples

Examples are sanitized. Raw contacts and URLs are redacted in this committed report.

### Highest Noise: Chatter Around Player/Gear Thread

- Thread: `My rig with Buddy Cage's`
- Role: `answer_advice`
- `noise_score`: 1.0
- `quality_score`: 0.488

```text
I hope you got to spend some time with Buddy ... ask Buddy if there's a place you can buy a NRPS T shirt ... Thanks ... 78 Emmons PP...
```

Issue: still high-noise social/player context. It passes the mechanical preflight gates, but it is not obviously clean answer evidence.

### Highest Noise: Chatter/String Thread

- Thread: `A bent string, is a spent string.`
- Role: `answer_advice`
- `noise_score`: 1.0
- `quality_score`: 0.428

```text
This thread's been hijacked ... sinistro'sal vagueries ... Legends Of The String Of Steel ... try unsharpening it...
```

Issue: the chunk has some answer-like terms but is mostly chatter. This argues for an additional quality/noise gate before a full embed candidate is approved.

### Highest Noise: Link/Contact Mechanical Thread

- Thread: `New here - Fender 400 mechanical issues`
- Role: `answer_advice`
- `noise_score`: 1.0
- `quality_score`: 0.428

```text
please post a picture or two ... [contact removed] if you want ... Where are you? ... long gear list removed or partially retained...
```

Issue: source-card safe after redaction, but still noisy answer text.

### Remaining Signature Candidate

- Thread: `Thanks  Mike Brown !`
- Role: `answer_advice`
- Leakage hit: `signature`
- `noise_score`: 0.56
- `quality_score`: 0.565

```text
Sent my old Session 500 to Peavey ... Darvin Willhoite ... I know of no other company that will still service a product they made 25 to 30 years ago...
```

Issue: this may be a false positive from a gear-dense post, or a true remaining long signature later in the chunk. It is below the threshold at sample scale but should be reviewed in full-corpus preflight.

### Remaining Signature Candidate

- Thread: `String 3 G# keeps breaking!! Please help.`
- Role: `answer_advice`
- Leakage hit: `signature`
- `noise_score`: 0.56
- `quality_score`: 0.723

```text
string on my G2 in over 2 years ... ARTIST RELATIONS: MSA GUITARS ... Mullen G2, Rittenberry S10, Infinity D10...
```

Issue: likely true signature/footer leakage. The current gate tolerates the large-sample rate, but this is a cleanup target before embedding approval.

## Assessment

Large-sample preflight now passes.

The fixes addressed the three reported blockers:

- Legacy UBB metadata completeness rose from `0.769` to `1.000`.
- Leakage rate dropped from `0.061` to `0.005`, under the strict threshold after rounding.
- Mixed-topic quarantine rate dropped from `0.123` to `0.000` because unresolved mixed-topic records are not emitted as answer evidence.

Full corpus-v2 generation is reasonable next only as a non-embedding generated-output step followed by full preflight. Embed-v2 remains blocked until full corpus-v2 preflight passes and the user explicitly approves the exact embedding command and v2 Chroma path.

## Commands Run

- `.venv/bin/python -m pytest tests/test_phase3_clean_classify_chunks.py tests/test_phase3_chunk_v2.py tests/test_phase3_embed_v2_preflight.py`
- `.venv/bin/python scripts/phase3_clean_classify_chunks.py --input /tmp/steel-rag-corpus-v2-large-preflight/large_input_sample.jsonl --output /tmp/steel-rag-corpus-v2-large-preflight/clean_classified_chunks.jsonl --report /tmp/steel-rag-corpus-v2-large-preflight/phase3b-large-report.md`
- `.venv/bin/python scripts/phase3_chunk_v2.py --input /tmp/steel-rag-corpus-v2-large-preflight/clean_classified_chunks.jsonl --output /tmp/steel-rag-corpus-v2-large-preflight/chunks-v2.jsonl --report /tmp/steel-rag-corpus-v2-large-preflight/phase3c-large-report.md --target-words 180 --max-words 240 --min-words 8`
- `.venv/bin/python scripts/phase3_embed_v2_preflight.py --clean-input /tmp/steel-rag-corpus-v2-large-preflight/clean_classified_chunks.jsonl --chunk-input /tmp/steel-rag-corpus-v2-large-preflight/chunks-v2.jsonl --target-chroma-path /Users/cory/Documents/Pocket\\ Steel/corpus-v2/vector-stores/chroma --planned-output-path /Users/cory/Documents/Pocket\\ Steel/corpus-v2/chunks-v2.jsonl --report /tmp/steel-rag-corpus-v2-large-preflight/phase3d-preflight-report.md --json-report /tmp/steel-rag-corpus-v2-large-preflight/phase3d-preflight.json`
- `.venv/bin/python - <<'PY' ... PY` to create `/tmp/steel-rag-corpus-v2-large-preflight/large_preflight_analysis_after_fixes.json`
- `.venv/bin/python -m pytest`

## Current V1 Chroma Statement

No embeddings were run. No embedding command was invoked. No v2 Chroma store was created. The current v1 Chroma store was not modified. `corpus-unified/chunks.jsonl` was read but not overwritten. Backend answer code, frontend code, and app configuration were not changed.
