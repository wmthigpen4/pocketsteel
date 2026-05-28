# Phase 3D Embed V2 Plan

Scope: plan a safe corpus-v2 embedding workflow for The Turnaround without running embeddings, creating a vector store, modifying v1 Chroma, changing backend/frontend code, or switching app configuration.

Task mode: GREEN for this planning document only. Any command that creates `corpus-v2` corpus outputs, writes a Chroma store, runs embeddings, or changes retrieval/app configuration requires explicit human approval under `AGENTS.md`.

## Goal

Phase 3D should build a new corpus-v2 vector store beside the current v1 store only after Phase 3B/3C outputs pass review. The current app stays on v1 unless v2 wins a later A/B evaluation and the user explicitly approves the config switch.

Current v1 paths remain untouched:

- v1 chunks: `/Users/cory/Documents/sgf-scrape-test/corpus-unified/chunks.jsonl`
- v1 Chroma: `/Users/cory/Documents/sgf-scrape-test/corpus-unified/vector-stores/chroma`
- v1 collection: `steel_guitar_unified`
- v1 vector count: `401,100`

## Intended V2 Paths

All Phase 3D artifacts should live beside v1, not inside v1:

| artifact | intended path |
| --- | --- |
| Cleaned/classified Phase 3B output | `corpus-v2/clean_classified_chunks.jsonl` |
| Chunker-v2 Phase 3C output | `corpus-v2/chunks-v2.jsonl` |
| New Chroma store | `corpus-v2/vector-stores/chroma` |
| Chroma collection | `steel_guitar_unified_v2` |
| Preflight report | `corpus-v2/reports/pre-embedding-checks.md` |
| Metadata audit | `corpus-v2/reports/chroma-metadata-audit.md` |
| Embedding build report | `corpus-v2/reports/embed-v2-build-report.md` |
| A/B eval report | `corpus-v2/reports/ab-eval-v1-v2.md` |

Before any generated output is written under `corpus-v2/`, confirm the generated path is ignored by git. At the time this plan was written, the visible ignore rules include Chroma paths under `rag-data/**/chroma/`, but not `corpus-v2/`. Phase 3D implementation should either use an already ignored external output directory or add a narrowly scoped ignore rule with approval before generating corpus-v2 artifacts.

## Required Pre-Embedding Checks

Run these checks against `corpus-v2/clean_classified_chunks.jsonl` and `corpus-v2/chunks-v2.jsonl` before any embedding command is approved.

### File And Lineage Checks

- Confirm both v2 input files exist and are generated from approved Phase 3B/3C scripts.
- Confirm `corpus-v2/chunks-v2.jsonl` is newer than or traceably derived from `corpus-v2/clean_classified_chunks.jsonl`.
- Record cleaner version, chunker version, command arguments, timestamp, and config hash in the report.
- Confirm no command reads from or writes to `/Users/cory/Documents/sgf-scrape-test/corpus-unified/vector-stores/chroma`.

### Chunk Count

- Count rows in `corpus-v2/chunks-v2.jsonl`.
- Compare v2 chunk count to v1 count `401,100`.
- Flag unexpectedly low counts as coverage risk.
- Flag unexpectedly high counts as chunking/noise or duplication risk.
- Require a human-readable explanation for any large delta by source system, forum, and thread category.

### Metadata Completeness

Every chunk should contain:

- `chunk_id`
- `source_system`
- `forum_name`
- `thread_id`
- `thread_title`
- `source_url`
- `post_uids`
- `chunk_text`
- `chunk_role`
- `post_role_summary`
- `quality_score`
- `noise_score`
- `cleanup_flags`
- `source_metadata_complete`

Before embedding, fail the preflight if:

- `chunk_id` is empty or duplicated.
- `chunk_text` is empty after trimming.
- `source_metadata_complete=false` exceeds a small reviewed exception threshold.
- Required scalar metadata cannot be serialized into Chroma metadata.

### Post Identity Completeness

- Count chunks with empty `post_uids`.
- Count chunks with one post UID vs multiple post UIDs.
- Sample multi-post chunks to confirm question/answer pairing is intentional.
- Require post identity exceptions to stay materially below the v1 known issue count of `148` chunks with `post_uids=[]`.

### Noise-Score Distribution

Report distribution buckets:

| bucket | meaning |
| --- | --- |
| `0.00-0.20` | clean or near-clean |
| `0.21-0.40` | mild noise, probably acceptable |
| `0.41-0.60` | review required before embedding |
| `0.61-0.80` | likely exclude or quarantine |
| `0.81-1.00` | do not embed without explicit exception |

Preflight should also report top cleanup flags, including:

- `top_removed`
- `duplicate_sentence_removed`
- `contact_block_removed`
- `signature_removed`
- `quote_heavy_flagged`
- `link_only`
- `question_unpaired`
- `mixed_topic_flagged`
- `oversized_split`

### Source URL Presence

- Count chunks with missing or blank `source_url`.
- Count malformed URLs.
- Sample source URLs across current phpBB and legacy UBB rows.
- Confirm source URLs are suitable for source-card display and do not expose raw contact/private details.

### Role Distribution

Report chunk counts by:

- `question`
- `answer_advice`
- `opinion`
- `gear_signature`
- `sale_wanted`
- `event`
- `memorial`
- `link_only`
- `joke_chatter`
- `contact_block`
- `unknown`

Expected embedding default:

- Embed `answer_advice` by default when quality thresholds pass.
- Consider `question` only when paired, high-context, or useful for retrieval diagnostics.
- Exclude or quarantine `gear_signature`, `contact_block`, `link_only`, `sale_wanted`, and `joke_chatter` from answer-oriented embeddings unless explicitly approved.
- Keep `event`, `memorial`, `opinion`, and `unknown` role handling visible in the report so A/B evaluation can detect coverage gaps.

### Sample Review Requirements

Before embedding, human review should inspect:

- At least `25` random high-quality `answer_advice` chunks.
- At least `25` chunks from high-noise buckets above `0.40`.
- At least `10` chunks each from `question`, `opinion`, `event`, `memorial`, and `unknown` if present.
- At least `10` chunks with multiple `post_uids`.
- At least `10` chunks with `oversized_split`.
- At least `10` chunks with `quote_heavy_flagged` or `mixed_topic_flagged`.
- Any chunk samples where raw email/contact details remain visible in `chunk_text`.

Approval should be blocked if reviewed source cards still show common v1 failures: `Top`, duplicated body text, raw `sp=sharing`, raw contact details, standalone link-only content, or signature-only excerpts promoted as answers.

## Planned Embedding Command

Do not run these commands yet. They are placeholders for the approved Phase 3D implementation.

First, run a preflight audit script that may need to be created in Phase 3D implementation:

```bash
.venv/bin/python scripts/phase3_embed_v2_preflight.py \
  --clean-input corpus-v2/clean_classified_chunks.jsonl \
  --chunk-input corpus-v2/chunks-v2.jsonl \
  --report corpus-v2/reports/pre-embedding-checks.md
```

Only if the preflight report passes and the user explicitly approves embedding, run a new v2 embed command that writes only to the v2 Chroma path:

```bash
.venv/bin/python scripts/phase3_embed_v2_chroma.py \
  --input corpus-v2/chunks-v2.jsonl \
  --chroma-path corpus-v2/vector-stores/chroma \
  --collection steel_guitar_unified_v2 \
  --report corpus-v2/reports/embed-v2-build-report.md
```

If the existing `rag_embed_chroma.py` is reused instead of a new wrapper, Phase 3D must first document the exact non-reset invocation and prove the output path points to `corpus-v2/vector-stores/chroma`, never the v1 path. Do not use any `--reset` flag against v1.

Required post-build checks after approved embedding:

- v2 vector count equals v2 chunk count.
- Chroma collection name is `steel_guitar_unified_v2`.
- v2 metadata contains scalar-safe source fields and role/quality fields.
- v1 Chroma file mtimes and vector count are unchanged.
- `corpus-v2/reports/chroma-metadata-audit.md` documents sample rows and metadata completeness.

## A/B Testing Plan

Phase 3E should compare v1 and v2 after, and only after, v2 is embedded beside v1.

Inputs:

- v1 Chroma: `/Users/cory/Documents/sgf-scrape-test/corpus-unified/vector-stores/chroma`
- v1 collection: `steel_guitar_unified`
- v2 Chroma: `corpus-v2/vector-stores/chroma`
- v2 collection: `steel_guitar_unified_v2`
- Shared question bank: `tests/fixtures/user_question_bank.json`
- Electronics eval bank: `eval/electronics_gold_questions.jsonl`

Compare each question with identical retrieval/answer settings except for index path and collection name.

Metrics:

- Retrieval relevance: whether top-k chunks directly support the question.
- Retrieval cleanliness: visible `Top`, duplicated body text, quote-only text, raw contacts, link-only content, and signatures.
- Source-card quality: title, forum, URL, readable excerpt, post identity, and absence of boilerplate.
- Answer directness: whether the generated answer addresses the question without wandering into classifieds/chatter.
- Grounding: whether claims can be traced to retrieved sources.
- Coverage: no-source, weak-source, and wrong-category rates by question type.
- Regression severity: categories where v2 loses a factual detail v1 retrieved correctly.

Suggested output:

- Raw v1 retrieval rows under an ignored eval output directory.
- Raw v2 retrieval rows under a separate ignored eval output directory.
- Paired answer outputs.
- `corpus-v2/reports/ab-eval-v1-v2.md` with per-question winner: `v1`, `v2`, `tie`, or `needs_review`.

V2 should not win only because it is cleaner. It must maintain or improve useful retrieval coverage while materially improving source cleanliness and source-card quality.

## Rollback And Switch Rules

- The app stays on v1 by default.
- No backend answer code changes are part of Phase 3D.
- No frontend changes are part of Phase 3D.
- No app config switch happens in Phase 3D.
- v2 is opt-in for local evaluation only until Phase 3E proves it wins.
- Phase 3F config switch requires explicit human approval after A/B results are reviewed.
- Rollback is simply leaving app configuration pointed at v1, or switching it back to:
  `/Users/cory/Documents/sgf-scrape-test/corpus-unified/vector-stores/chroma`

If v2 fails preflight, embedding should not start. If v2 fails A/B evaluation, keep v1 as production and archive the v2 reports for future cleanup work.

## Risks

- `corpus-v2/` is not currently visible in ignore rules, so generated v2 corpus/vector outputs could become accidental git candidates unless ignore handling is approved first.
- A stricter chunker may reduce noisy retrieval while also dropping useful historical, classifieds-adjacent, event, or memorial context.
- Question/answer pairing can improve answerability but may accidentally merge unrelated nearby posts if thread structure is messy.
- Embedding v2 will consume disk and time even though it is separate from v1.
- Reusing existing embedding code without a wrapper increases the risk of passing the wrong Chroma path or reset flag.

## Exact Human Approval Required Before Embedding

Before any embedding command runs, the user must explicitly approve all of the following:

- The final `corpus-v2/chunks-v2.jsonl` preflight report.
- The v2 Chroma output path: `corpus-v2/vector-stores/chroma`.
- The v2 collection name: `steel_guitar_unified_v2`.
- The exact embedding command and embedding model.
- Permission to create a new vector store beside v1.
- Confirmation that no app config switch is included in Phase 3D.

Approval to plan Phase 3D is not approval to embed.

## Recommended Phase 3D Implementation Prompt

```text
Begin Phase 3D embed-v2 implementation preflight for The Turnaround corpus-v2.

This is YELLOW/RED-adjacent. Do not run embeddings until the preflight report is complete and I explicitly approve the exact embedding command.

Use:
- docs/phase-3-corpus-cleanup-plan.md
- docs/phase-3a-corpus-profile.md
- docs/phase-3b-cleaner-classifier-report.md
- docs/phase-3c-chunker-v2-report.md
- docs/phase-3d-embed-v2-plan.md
- scripts/phase3_clean_classify_chunks.py
- scripts/phase3_chunk_v2.py

Do not modify v1 Chroma, reset Chroma, regenerate embeddings, run embedding commands, delete corpus files, run live SGF scraping, overwrite corpus-unified/chunks.jsonl, change backend answer code, change frontend code, or switch app config.

Create a Phase 3D preflight/audit script and report for corpus-v2 inputs. Verify chunk count, required metadata, post identity, noise-score distribution, source URL presence, role distribution, gitignore safety, and sample-review blockers. Produce only reports or small sample-safe output. Stop before any embedding command and ask for explicit approval with the exact command.

End with files changed, tests run, risks, human decision needed, recommended next step, and explicit confirmation that no embeddings were run and v1 Chroma was not modified.
```

## Closeout

Files changed:

- `docs/phase-3d-embed-v2-plan.md`

Commands run:

- `pwd && git branch --show-current && git status --short`
- `sed -n '1,220p' docs/phase-3-corpus-cleanup-plan.md`
- `sed -n '1,260p' docs/phase-3a-corpus-profile.md`
- `sed -n '1,260p' docs/phase-3b-cleaner-classifier-report.md`
- `sed -n '1,260p' docs/phase-3c-chunker-v2-report.md`
- `rg --files | rg '(^scripts/phase3_|^tests/fixtures/|^tests/test_phase3_|^eval/|user_question_bank)'`
- `sed -n '220,520p' docs/phase-3-corpus-cleanup-plan.md`
- `rg -n "corpus-v2|corpus-v2-samples|vector-stores|chroma|corpus-unified|sgf-scrape-test" .gitignore .git/info/exclude 2>/dev/null`
- `ls -ld corpus-v2 corpus-v2-samples 2>/dev/null || true`

Risks:

- Embedding remains blocked until preflight and explicit approval.
- The intended generated output path needs ignore-safety handling before writing corpus-v2 artifacts.
- A clean v2 index could still regress coverage unless Phase 3E A/B testing passes.

Explicit confirmation:

- No embeddings were run.
- No embedding command was invoked.
- The current v1 Chroma store was not modified.
- `corpus-unified/chunks.jsonl` was not overwritten.
- Backend answer code, frontend code, scraper behavior, and app configuration were not changed.
