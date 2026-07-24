# Phase 3B Cleaner Classifier Report

Scope: implement and test a sample-safe cleaner/classifier for corpus-v2 derived outputs. This phase does not run a full corpus rebuild, does not chunk v2, and does not embed anything.

## What Changed

- Added `scripts/phase3_clean_classify_chunks.py`.
- Added focused tests in `tests/test_phase3_clean_classify_chunks.py`.
- Added a tiny sample fixture at `tests/fixtures/phase3_sample_chunks.jsonl`.
- Generated a sample output only under `/tmp/steel-rag-corpus-v2-sample/`.

The script reads JSONL chunk-like rows and writes derived rows with:

- `raw_text`
- `clean_text`
- `answer_text`
- `signature_text`
- `post_role`
- `chunk_role`
- `detected_roles`
- `noise_score`
- `answer_density`
- `source_metadata_complete`
- `missing_source_metadata`
- `post_identity_complete`
- `quality_score`
- `cleanup_flags`

## Cleaner Rules Implemented

- Removes `Top`, `Back to top`, attachment permission text, and edit notice lines.
- Collapses repeated sentences caused by `Top` duplication.
- Removes `sp=sharing` and `usp=sharing` share fragments.
- Redacts raw emails, phone numbers, and direct contact phrases from `answer_text`.
- Splits classic signature separators and short gear-list signatures into `signature_text`.
- Detects quote markers for noise scoring.
- Removes standalone repeated thread-title lines.
- Detects question-only, answer/advice-like, sale/wanted, event, memorial, link-only, joke/chatter, contact-block, gear-signature, opinion, and unknown roles.

## Sample Classifier Run

Command:

```bash
.venv/bin/python scripts/phase3_clean_classify_chunks.py \
  --input tests/fixtures/phase3_sample_chunks.jsonl \
  --output /tmp/steel-rag-corpus-v2-sample/clean_classified_chunks.jsonl \
  --report /tmp/steel-rag-corpus-v2-sample/report.md
```

Sample role counts:

| role | count |
| --- | ---: |
| `answer_advice` | 1 |
| `contact_block` | 1 |
| `gear_signature` | 1 |
| `question` | 1 |
| `sale_wanted` | 1 |

Sample cleanup flag counts:

| cleanup flag | count |
| --- | ---: |
| `contact_block_removed` | 1 |
| `duplicate_sentence_removed` | 1 |
| `signature_removed` | 1 |
| `top_removed` | 1 |

Sample averages:

- Average noise score: `0.236`
- Average answer density: `0.132`

## Before And After Samples

### Top Duplication

Before:

```text
Rick / 1 Jan 2007 1:00 pm Try a grounded outlet first. Top Try a grounded outlet first.
```

After:

```text
Rick / 1 Jan 2007 1:00 pm Try a grounded outlet first.
```

Role: `answer_advice`

Flags: `duplicate_sentence_removed`, `top_removed`

### Contact Block

Before:

```text
I can help with that processor. Email me at picker@example.com or call 615-555-1212.
```

After:

```text
I can help with that processor. [contact removed] at [contact removed] or call [contact removed].
```

Role: `contact_block`

Flags: `contact_block_removed`

### Signature

Before:

```text
Use a 500K pot if that is what the pedal expects.
------------------
Zum D-10, Nashville 400, Goodrich volume pedal
```

After:

```text
Use a 500K pot if that is what the pedal expects.
```

Role: `gear_signature`

Flags: `signature_removed`

### Question

Before:

```text
Does anyone know what speaker came in a Sho-Bud Compactra amp?
```

After:

```text
Does anyone know what speaker came in a Sho-Bud Compactra amp?
```

Role: `question`

Flags: none

### Sale/Wanted

Before:

```text
For sale: Goodrich volume pedal, $100 plus shipping. PM sent.
```

After:

```text
For sale: Goodrich volume pedal, $100 plus shipping. PM sent.
```

Role: `sale_wanted`

Flags: none

## Tests

Targeted test command:

```bash
.venv/bin/python -m pytest tests/test_phase3_clean_classify_chunks.py
```

Result: `9 passed`.

Full test command:

```bash
.venv/bin/python -m pytest
```

Result: `114 passed`.

## Known Limits

- This is a sample-safe cleaner/classifier, not a full corpus-v2 rebuild.
- It does not yet group question posts with answer posts; that belongs in Phase 3C chunker-v2.
- It does not embed anything.
- It does not alter retrieval, backend answer behavior, frontend behavior, or app configuration.

## Recommended Phase 3C Chunker-V2 Prompt

```text
Begin Phase 3C chunker-v2 planning for Steel Guitar RAG corpus-v2.

This is YELLOW. Stop after presenting the implementation plan and proposed diff unless explicitly approved to apply it.

Use:
- docs/phase-3-corpus-cleanup-plan.md
- docs/phase-3a-corpus-profile.md
- docs/phase-3b-cleaner-classifier-report.md
- scripts/phase3_clean_classify_chunks.py

Do not modify v1 Chroma, reset Chroma, regenerate embeddings, delete corpus files, run live SGF scraping, overwrite corpus-unified/chunks.jsonl, change backend answer code, change frontend code, or switch app config.

Design chunker-v2 that reads only derived cleaner/classifier output under corpus-v2 or a sample-safe path. It should:
- group question posts with nearby answer_advice posts where possible
- avoid standalone link_only, sale_wanted, joke_chatter, contact_block, and gear_signature chunks for answer embeddings
- split oversized and mixed-topic content
- carry post_role, chunk_role, cleanup_flags, answer_density, noise_score, source_metadata_complete, quality_score, source metadata, and post identity
- produce sample-safe output and tests first

Do not embed anything. End with files changed, tests run, risks, human decision needed, recommended next step, and explicit confirmation that v1 Chroma was not modified.
```

## Current V1 Chroma Statement

The current v1 Chroma store was not modified. This Phase 3B work did not reset Chroma, regenerate embeddings, delete corpus files, run live SGF scraping, overwrite `corpus-unified/chunks.jsonl`, change backend answer code, change frontend code, or switch app config.
