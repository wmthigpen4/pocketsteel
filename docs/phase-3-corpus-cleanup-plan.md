# Phase 3 Corpus Cleanup Plan

Scope: plan a safe `corpus_v2` cleanup and rebuild for The Turnaround without modifying the current production Chroma store, current `corpus-unified/chunks.jsonl`, scraper behavior, backend answer code, or raw corpus data.

Task mode: GREEN for this planning document. Later implementation phases that change chunking, corpus outputs, embedding outputs, or app configuration require explicit approval under `AGENTS.md`.

## Current State

The current unified SGF index is usable for read-only retrieval smoke tests, but it is not production-quality signed off. Existing audits show:

- Current v1 chunks: `~/Documents/sgf-scrape-test/corpus-unified/chunks.jsonl`
- Current v1 Chroma store: `~/Documents/sgf-scrape-test/corpus-unified/vector-stores/chroma`
- Current v1 Chroma SQLite: `~/Documents/sgf-scrape-test/corpus-unified/vector-stores/chroma/chroma.sqlite3`
- Current Chroma collection: `steel_guitar_unified`
- Embedded vectors: `401,100`
- Chunk rows: `401,100`
- Current chunk issue report: `~/Documents/sgf-scrape-test/corpus-unified/reports/unified_chunk_issues.tsv`

Known v1 quality risks from `docs/embedding-audit.md`, `docs/chunk-quality-triage.md`, and the unified review report:

- `Top` and other phpBB navigation text remains in many chunks.
- Some current phpBB chunks duplicate post body text inside the same chunk.
- Some chunks include raw share fragments such as `sp=sharing`.
- Some chunks preserve signatures, gear lists, email/contact blocks, quotes, and link lists as if they were primary answer content.
- Tiny chunks can be question-only, link-only, sales-only, or chatter-only.
- Oversized chunks can mix too many posts and drift across topic roles.
- Chroma metadata lacks scalar `post_uid`, while chunks use `post_uids`.

## Current Inputs

Raw parsed SGF JSONL:

- Current phpBB parsed thread JSONL: `~/Documents/sgf-scrape-test/sgf-output/jsonl/forum-{forum_id}/*.jsonl`
- Current phpBB manifest: `~/Documents/sgf-scrape-test/sgf-output/manifest.sqlite`
- Forums present in parsed JSONL: `forum-5`, `forum-8`, `forum-11`, `forum-13`, `forum-15`, `forum-21`, `forum-22`, `forum-27`, `forum-31`, `forum-34`, `forum-35`

Current clean corpus files used by the unified build:

- Current phpBB clean posts: `~/Documents/sgf-scrape-test/corpus-clean/current-phpbb/clean_posts.jsonl`
- Current phpBB skipped posts: `~/Documents/sgf-scrape-test/corpus-clean/current-phpbb/skipped_posts.jsonl`
- Current phpBB clean report: `~/Documents/sgf-scrape-test/corpus-clean/current-phpbb/clean_corpus_report.json`
- Legacy UBB clean posts: `~/Documents/sgf-scrape-test/corpus-clean/legacy-ubb/clean_posts.jsonl`
- Legacy UBB skipped posts: `~/Documents/sgf-scrape-test/corpus-clean/legacy-ubb/skipped_posts.jsonl`
- Legacy UBB clean report: `~/Documents/sgf-scrape-test/corpus-clean/legacy-ubb/clean_corpus_report.json`

Current unified corpus files:

- Unified corpus SQLite: `~/Documents/sgf-scrape-test/corpus-unified/unified_corpus.sqlite`
- Unified corpus manifest: `~/Documents/sgf-scrape-test/corpus-unified/unified_corpus_manifest.jsonl`
- Unified threads manifest: `~/Documents/sgf-scrape-test/corpus-unified/unified_threads_manifest.jsonl`
- Unified build report: `~/Documents/sgf-scrape-test/corpus-unified/reports/unified_build_report.md`
- Unified review report: `~/Documents/sgf-scrape-test/corpus-unified/reports/unified_review_report.md`

Current v1 retrieval artifacts:

- Current chunks JSONL: `~/Documents/sgf-scrape-test/corpus-unified/chunks.jsonl`
- Current Chroma path: `~/Documents/sgf-scrape-test/corpus-unified/vector-stores/chroma`

## Target V2 Outputs

All Phase 3 outputs should be written beside v1, not over v1:

- `corpus-v2/clean_corpus.jsonl`
- `corpus-v2/chunks.jsonl`
- `corpus-v2/vector-stores/chroma`
- `corpus-v2/reports/profile-v1.md`
- `corpus-v2/reports/cleaner-classifier-report.md`
- `corpus-v2/reports/chunk-quality-report.md`
- `corpus-v2/reports/embedding-audit.md`
- `corpus-v2/reports/ab-eval-v1-v2.md`
- `corpus-v2/reports/samples/` for small, reviewable JSONL or Markdown samples

The v2 artifacts should include enough metadata to compare against v1 without reading from the v1 Chroma store:

- stable source IDs: `source_system`, `forum_id`, `forum_name`, `thread_id`, `thread_title`, `thread_url`, `post_uid`
- derived role metadata: `post_role`, `chunk_role`
- quality metadata: `answer_density`, `noise_score`, `source_metadata_complete`, `entity_match`, `thread_category`
- original provenance: source clean file path or source row ID where available
- v2 lineage: cleaner version, chunker version, build timestamp, and config hash

## Cleanup Rules

The cleaner should be conservative and auditable. It should preserve raw inputs exactly, write cleaned text only to `corpus-v2/clean_corpus.jsonl`, and record each dropped or transformed pattern in an audit field such as `cleanup_actions`.

Forum boilerplate:

- Drop phpBB navigation and profile scaffolding, including `Top`, `Back to top`, author profile labels, attachment permission text, edit notices, and repeated page chrome.
- Drop repeated author/date/header lines when they are clearly wrappers, not user content.
- Keep dates and usernames in metadata; avoid repeating them inside every cleaned text body unless needed for chunk display.

`Top`:

- Remove standalone `Top` lines.
- Remove inline duplication patterns such as `... text. Top ... same text.` by retaining one body copy and recording `removed_inline_top_duplicate`.
- Do not remove the word `top` when it is normal prose, for example `top string`, `top players`, or `top changer finger`.

`sp=sharing`:

- Strip raw Google Drive or similar share-query fragments from visible text.
- Preserve the normalized URL in `links` metadata when the link is useful.
- Increase `noise_score` when a chunk contains raw share URLs without explanatory text.

Signatures:

- Detect classic signature separators, repeated gear lists, homepage-only tails, and name/contact sign-offs.
- Move likely equipment signatures into `signature_text` or classify them as `gear_signature` instead of embedding them as primary advice.
- Keep gear details in primary text only when they directly answer the thread, for example an amp setting or copedent in the body of an answer.

Email/contact blocks:

- Remove raw email addresses, phone-like contact lines, mailing addresses, and "email me" blocks from embed text.
- Preserve a redacted indicator in metadata such as `removed_contact_block=true`.
- Do not expose personal contact details in v2 source cards unless later approved.

Quote blocks:

- Drop quote-only posts.
- Remove nested quote blocks when the post adds little or no new text.
- Preserve short quotes only when needed to understand a direct answer, and score them as higher noise than original author content.
- Track `quote_ratio` and use it in `noise_score`.

Repeated thread titles:

- Remove repeated thread titles from post bodies and chunk bodies when the same value already exists in `thread_title`.
- Do not remove title-like phrases if they are part of a sentence or a model/product name.

Question-only chunks:

- Keep the question text in the clean corpus.
- Avoid emitting standalone question-only chunks unless the question has strong entity or problem framing and no answer exists nearby.
- Prefer pairing a question post with the first one to three substantive answers when the thread structure supports it.
- Classify standalone questions as `chunk_role=question` and down-rank them for answer generation unless the query is asking for examples of questions.

Link-only chunks:

- Drop link-only chunks from embedding output unless the surrounding text names the resource and explains why it matters.
- Preserve link metadata for source cards and audit reports.
- Classify as `link_only` when retained for review or navigation.

Sales, wanted, and chatter:

- Classify classified-ad, wanted-to-buy, price-only, sold/bump/PM-sent, joke, condolence-only, and social chatter posts before chunking.
- Exclude `sale_wanted` and `joke_chatter` from answer-oriented embeddings unless they contain durable product, maintenance, or player-history information.
- Keep memorial and event content only when the target answer experience should support those categories; otherwise isolate them with role metadata so they can be filtered.

## Role Classification

Every retained post should receive a `post_role`. Every emitted chunk should receive a `chunk_role`, derived from the dominant post roles and the chunk's actual text.

Role labels:

- `question`: asks a specific technical, musical, historical, buying, or identification question without giving a substantive answer.
- `answer_advice`: provides actionable advice, factual explanation, troubleshooting, settings, technique, maintenance guidance, or experience-backed answer content.
- `opinion`: expresses preference, taste, ranking, disagreement, or subjective comparison without much durable technical detail.
- `gear_signature`: mostly a signature, rig list, equipment footer, website footer, or repeated identity block.
- `sale_wanted`: for-sale, wanted-to-buy, sold, bump, PM sent, price, shipping, classifieds logistics.
- `event`: announcement, show, convention, jam, concert, schedule, or trip report where event details are the main content.
- `memorial`: obituary, remembrance, condolence, tribute, health update, or death notice.
- `link_only`: mostly one or more links with little explanatory text.
- `joke_chatter`: jokes, banter, thanks-only, greetings, non-answer chatter, or off-topic social remarks.
- `unknown`: retained when the classifier is unsure; include this in audit samples.

Suggested chunk-role precedence:

- If a chunk has at least one high-density `answer_advice` post and noise is acceptable, use `answer_advice`.
- If a chunk starts with a question and contains direct answers, use `answer_advice` plus `contains_question=true`.
- If a chunk is mostly a question and lacks answers, use `question`.
- If low-value roles dominate token count, use that role even if a small amount of advice appears.
- If no role exceeds confidence thresholds, use `unknown` and sample it for review.

## Quality Scoring

Each post and chunk should get transparent numeric or boolean fields. Initial scoring can be heuristic; later eval can tune thresholds.

`answer_density`:

- Range: `0.0` to `1.0`.
- Increase for explanatory verbs, advice markers, named parts, amp/effects/settings/copedent terms, causal language, measured comparisons, and problem-solution phrasing.
- Decrease for questions, quotes, thanks, jokes, links without explanation, signatures, and classifieds logistics.

`noise_score`:

- Range: `0.0` to `1.0`.
- Increase for boilerplate, repeated text, `Top`, quote ratio, URL ratio, email/contact blocks, signature ratio, raw date/header repetition, `sp=sharing`, and duplicate n-grams.
- Gate chunks with high `noise_score` into review or exclusion.

`source_metadata_complete`:

- Boolean plus optional missing-field list.
- Required fields: `source_system`, `forum_name`, `thread_id`, `thread_title`, `thread_url`, and either scalar `post_uid` or nonempty `post_uids`.
- Chroma metadata for v2 should include scalar-friendly values and JSON-encoded arrays where needed.

`entity_match`:

- Range: `0.0` to `1.0` or enum `none`, `weak`, `strong`.
- Measures whether the chunk's entities align with the thread title, forum category, and likely query topic.
- Use for spotting mixed-topic chunks and source-card drift.

`thread_category`:

- Reuse existing categories where possible, such as `tone_amp_effects`, `electronics_repair`, `technique_instruction`, `copedent_tuning`, `mechanical_builder_info`, `player_history`, `recording`, `tab_or_arrangement`, `event`, `memorial_obituary`, and `unknown_review`.
- Add role-aware categories only with approval and migration notes.

## A/B Evaluation

Compare v1 and v2 side by side after v2 embedding is approved and built beside v1.

Evaluation setup:

- v1 Chroma: `~/Documents/sgf-scrape-test/corpus-unified/vector-stores/chroma`
- v1 collection: `steel_guitar_unified`
- v2 Chroma: `corpus-v2/vector-stores/chroma`
- v2 collection: `steel_guitar_unified_v2`
- Question bank: `tests/fixtures/user_question_bank.json`
- Electronics legacy eval bank: `eval/electronics_gold_questions.jsonl`

Metrics:

- Retrieval relevance: judge top-k chunks for direct support of the question.
- Source cleanliness: count visible boilerplate, `Top`, duplicated text, raw contact details, quote-only text, and link-only chunks.
- Answer quality: score directness, groundedness, specificity, practical usefulness, and hallucination risk.
- Source-card quality: score title, URL, forum, excerpt readability, author/date usefulness, and absence of raw boilerplate.
- Coverage: track no-source or weak-source rates by category.
- Regression guard: v2 must not lose important answer coverage for electronics, maintenance, copedent, player/entity, brand comparison, and safety questions.

Comparison method:

- Run identical queries against v1 and v2 with the same embedding model, top-k, and answer provider settings.
- Save raw retrieved rows and generated answers under separate timestamped eval output directories.
- Produce a paired report showing per-question winner: `v1`, `v2`, `tie`, or `needs_review`.
- Require human spot checks for samples where v2 wins automatically because of cleaner sources but loses a specific factual detail.

Switch criteria:

- v2 has lower visible noise in retrieved excerpts and source cards.
- v2 maintains or improves retrieval relevance on the existing question bank.
- v2 answer quality is at least tied overall and better on noisy-source categories.
- No category has a severe regression without an explicit acceptance note.
- v2 Chroma count, metadata completeness, and chunk audit pass.

## Implementation Phases

### Phase 3A: Read-Only Profiling

Approval needed: no, if strictly read-only and writing only a report/doc is approved for the task.

Actions:

- Profile v1 clean posts, unified chunks, chunk issue TSV, and sample retrieved chunks.
- Produce counts by forum, source system, thread category, issue type, role-like heuristic, and noise pattern.
- Sample examples for each cleanup rule.
- Do not write corpus outputs, embeddings, or Chroma data.

Exit criteria:

- Report confirms exact v2 source inputs.
- Report estimates the likely impact of dropping or reclassifying noisy content.
- Human approves moving to cleaner/classifier implementation.

### Phase 3B: Cleaner and Classifier

Approval needed: yes, because this changes derived corpus generation.

Actions:

- Implement a v2 cleaner/classifier that reads existing clean posts or raw parsed JSONL.
- Emit `corpus-v2/clean_corpus.jsonl` and cleaner audit reports only.
- Add tests for boilerplate removal, signature/contact handling, quote handling, link-only classification, and role classification.

Exit criteria:

- Clean corpus row counts and skip/classification reasons are auditable.
- No raw data is modified.
- v1 files remain untouched.

### Phase 3C: Chunker V2

Approval needed: yes, because this changes chunking.

Actions:

- Build chunker v2 from `corpus-v2/clean_corpus.jsonl`.
- Prefer question-plus-answer grouping for forum threads.
- Avoid standalone low-value chunks.
- Emit `corpus-v2/chunks.jsonl` and chunk audit reports.

Exit criteria:

- Chunk sizes stay within target bounds except documented exceptions.
- `chunk_role`, quality scores, and source metadata are present.
- Sample source cards are visibly cleaner than v1.

### Phase 3D: Embed V2 Beside V1

Approval needed: yes, because this creates a new vector store.

Actions:

- Embed only from `corpus-v2/chunks.jsonl`.
- Write only to `corpus-v2/vector-stores/chroma`.
- Use a new collection name such as `steel_guitar_unified_v2`.
- Never use `--reset` on the v1 Chroma path.

Exit criteria:

- v2 vector count matches v2 chunk count.
- v2 Chroma metadata audit passes.
- v1 Chroma path remains unchanged.

### Phase 3E: A/B Eval

Approval needed: yes, if generating eval outputs or invoking local answer services; no app config switch.

Actions:

- Run paired v1/v2 retrieval and answer evals using the existing question banks.
- Compare retrieval relevance, source cleanliness, answer quality, and source-card quality.
- Write `corpus-v2/reports/ab-eval-v1-v2.md`.

Exit criteria:

- Human-readable winner/needs-review table exists.
- Any v2 regressions are listed with severity.

### Phase 3F: Switch App Config If V2 Wins

Approval needed: yes, because this changes app/runtime configuration.

Actions:

- Point app config or environment documentation to v2 Chroma only after v2 wins.
- Keep v1 rollback instructions.
- Do not change backend answer behavior as part of this phase unless separately approved.

Exit criteria:

- Runtime can select v2.
- Rollback to v1 is documented.
- v1 store is still present and unmodified.

## Guardrails

- Do not modify `~/Documents/sgf-scrape-test/corpus-unified/vector-stores/chroma`.
- Do not reset Chroma.
- Do not regenerate embeddings until Phase 3D is explicitly approved.
- Do not delete corpus files.
- Do not run live SGF scraping.
- Do not overwrite `~/Documents/sgf-scrape-test/corpus-unified/chunks.jsonl`.
- Do not change backend answer code.
- Do not commit raw data, SQLite databases, vector stores, embeddings, logs, private transcripts, paid transcripts, or licensing metadata dumps.

## Exact Next Implementation Prompt

Use this prompt for the next phase:

```text
Begin Phase 3A read-only corpus profiling for The Turnaround.

Task mode: GREEN only if strictly read-only.

Do not modify Chroma, reset Chroma, regenerate embeddings, delete corpus files, run live SGF scraping, overwrite corpus-unified/chunks.jsonl, or change backend answer code.

Inspect these inputs:
- ~/Documents/sgf-scrape-test/corpus-clean/current-phpbb/clean_posts.jsonl
- ~/Documents/sgf-scrape-test/corpus-clean/legacy-ubb/clean_posts.jsonl
- ~/Documents/sgf-scrape-test/corpus-unified/chunks.jsonl
- ~/Documents/sgf-scrape-test/corpus-unified/reports/unified_chunk_issues.tsv
- ~/Documents/sgf-scrape-test/corpus-unified/unified_corpus.sqlite in read-only mode

Create a read-only profiling report at docs/phase-3a-corpus-profile.md that estimates counts and representative samples for:
- forum boilerplate and Top duplication
- sp=sharing and link-only chunks
- signatures and gear-signature tails
- email/contact blocks
- quote-heavy chunks
- repeated thread titles and duplicate body text
- question-only chunks
- sales/wanted/chatter
- proposed post_role and chunk_role distribution
- proposed quality-score distributions

End with files changed, tests run, risks, human decision needed, recommended next step, and explicit confirmation that v1 Chroma was not modified.
```

## Current V1 Chroma Statement

This plan does not modify the current v1 Chroma store. The current v1 path remains `~/Documents/sgf-scrape-test/corpus-unified/vector-stores/chroma`, and the v2 plan keeps all new vector data under `corpus-v2/vector-stores/chroma`.
