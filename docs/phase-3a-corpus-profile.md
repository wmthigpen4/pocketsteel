# Phase 3A Corpus Profile

Scope: read-only profile of the current Steel Guitar RAG unified corpus and chunks for Phase 3 cleanup planning. This report follows `docs/phase-3-corpus-cleanup-plan.md`.

No Chroma store, embedding output, scraper output, corpus file, backend code, or frontend code was modified.

## Inputs Profiled

- Chunk source: `/Users/cory/Documents/sgf-scrape-test/corpus-unified/chunks.jsonl`
- SQLite mirror: `/Users/cory/Documents/sgf-scrape-test/corpus-unified/unified_corpus.sqlite`, opened with `mode=ro`
- Issue TSV: `/Users/cory/Documents/sgf-scrape-test/corpus-unified/reports/unified_chunk_issues.tsv`
- Current v1 Chroma path, not opened for writes: `/Users/cory/Documents/sgf-scrape-test/corpus-unified/vector-stores/chroma`

## Summary

- Total chunk count: `401,100`
- Full-profiled chunk count: `401,100`
- Representative sample rows queried: `48`
- Representative sample rows shown below: `16`
- Estimated noisy/risky chunks: `284,787`
- Estimated noise rate: `71.0%`
- Estimated answer-quality risk chunks, excluding mostly tolerable signature/event-only cases: `261,444`
- Token estimate range: `1` to `1,703`
- Average token estimate: `719.89`

The buckets below are heuristic and overlapping. A chunk can count in more than one bucket, especially because current chunks often contain multiple posts, repeated text, and answer-like content in the same row.

## Corpus Shape

By source system:

| source system | chunks |
| --- | ---: |
| `sgf_phpbb_current` | 332,982 |
| `sgf_ubb_legacy` | 68,118 |

By forum:

| forum | chunks |
| --- | ---: |
| Pedal Steel | 124,930 |
| Steel Players | 102,923 |
| Electronics | 77,581 |
| Steel on the Web | 34,154 |
| Steel Without Pedals | 25,549 |
| Tablature | 15,687 |
| No Peddlers | 12,731 |
| Recording | 3,724 |
| New Product Announcements | 1,422 |
| Band-in-a-Box | 1,237 |
| Builders' Corner | 942 |
| Slide Guitar and String Bender Guitars | 220 |

By current thread category:

| category | chunks |
| --- | ---: |
| `tone_amp_effects` | 173,059 |
| `recording` | 60,000 |
| `copedent_tuning` | 42,153 |
| `technique_instruction` | 41,477 |
| `electronics_repair` | 22,345 |
| `player_history` | 18,643 |
| `tab_or_arrangement` | 14,194 |
| `unknown_review` | 14,164 |
| `music_theory` | 4,608 |
| `mechanical_builder_info` | 4,175 |
| `band_in_a_box` | 3,863 |
| `gear_setup` | 1,936 |
| `memorial_obituary` | 483 |

Current issue TSV counts:

| issue type | count |
| --- | ---: |
| `junk_phrase` | 46,735 |
| `tiny_chunk` | 9,058 |
| `huge_chunk` | 4,889 |
| `very_tiny_chunk` | 839 |

## Counts By Bucket

| bucket | count | answer-quality risk |
| --- | ---: | --- |
| `top_navigation_artifacts` | 91,227 | High |
| `sp_sharing_fragments` | 82 | Medium |
| `link_only_chunks` | 1,886 | High |
| `email_contact_blocks` | 43,020 | High |
| `signature_gear_list` | 43,201 | Medium |
| `quote_heavy_chunks` | 75,260 | High |
| `repeated_title_or_body` | 56,863 | High |
| `question_only_chunks` | 16,738 | High |
| `answer_advice_like_chunks` | 359,078 | Usually useful |
| `sales_wanted_chatter` | 75,847 | Medium to high |
| `event_memorial_chunks` | 23,523 | Usually filterable |
| `tiny_low_value_chunks` | 19,887 | High |
| `oversized_chunks` | 7,394 | High |
| `missing_source_metadata` | 0 | Low |
| `missing_post_identity` | 148 | Medium |
| `mixed_topic_content` | 78,031 | High |

Notes:

- `answer_advice_like_chunks` is intentionally broad. It means the chunk contains at least one advice or technical marker, not that the whole chunk is clean.
- `signature_gear_list` uses a refined count: exact signature separators plus short multi-gear tails. A broader SQL `LIKE` attempt overcounted because `_` is a wildcard in SQLite `LIKE`.
- `email_contact_blocks` is deliberately conservative for privacy/source-card risk; Phase 3B should separate raw email addresses from benign words like "email".
- `missing_post_identity` counts chunks with `post_uids='[]'`. Chroma v1 also lacks scalar `post_uid` metadata, already documented in `docs/embedding-audit.md`.

## Representative Examples

| bucket | chunk | why it matters |
| --- | --- | --- |
| `top_navigation_artifacts` | `sgf_phpbb_current:forum-11:thread-100231:chunk-0006` / Electronics / `Crate Power Block Amp = Zero Point Energy Source???` | Contains inline `Top` followed by duplicated post body text. |
| `sp_sharing_fragments` | `sgf_phpbb_current:forum-11:thread-326567:chunk-0006` / Electronics / `Pedal Board Solutions?` | Contains raw share-link fragments; useful link metadata should be preserved outside embed text. |
| `link_only_chunks` | `sgf_phpbb_current:forum-11:thread-100614:chunk-0001` / Electronics / `Fender Steel King on ebay` | Short mostly-link chunk: "I saw this on ebay... click here" duplicated around `Top`. |
| `email_contact_blocks` | `sgf_phpbb_current:forum-11:thread-132912:chunk-0001` / Electronics / `Lexcon MPX1` | Includes a visible raw email address in the chunk body. |
| `signature_gear_list` | `sgf_phpbb_current:forum-11:thread-103508:chunk-0001` / Electronics / `Sho-Bud Pickup Question` | Includes useful answer text mixed with rig/signature-like gear list material. |
| `quote_heavy_chunks` | `sgf_phpbb_current:forum-11:thread-100358:chunk-0002` / Electronics / `vibrator for steel?` | Quote/chatter-heavy row with low durable answer value. |
| `repeated_title_or_body` | `sgf_phpbb_current:forum-11:thread-100314:chunk-0001` / Electronics / `Standel S-80 head` | Question body repeats around `Top`, which pollutes retrieved excerpts. |
| `question_only_chunks` | `sgf_phpbb_current:forum-11:thread-100018:chunk-0001` / Electronics / `QA issues` | Mostly asks whether quality issues were fixed; no substantive answer in the same chunk. |
| `answer_advice_like_chunks` | `sgf_phpbb_current:forum-11:thread-100016:chunk-0001` / Electronics / `Vegas 400 reverb problem` | Has real troubleshooting/advice signals and should be retained, but still needs de-duplication. |
| `sales_wanted_chatter` | `sgf_phpbb_current:forum-11:thread-100013:chunk-0001` / Electronics / `help with search` | Non-answer forum support/chatter can match user queries but should not dominate answer retrieval. |
| `event_memorial_chunks` | `sgf_phpbb_current:forum-11:thread-243634:chunk-0001` / Electronics / `hundreds of tubes!` | Memorial/category and inherited-gear context may be useful sometimes, but should be classified separately. |
| `tiny_low_value_chunks` | `sgf_phpbb_current:forum-11:thread-100521:chunk-0001` / Electronics / `Sho-Bud Compactra 100 Amp` | Small question-like chunk; useful only if paired with answers. |
| `oversized_chunks` | `sgf_phpbb_current:forum-11:thread-101699:chunk-0002` / Electronics / `zxzz` | 1,608-token chunk with safety/electrical advice, boilerplate, edit text, and repetition. |
| `missing_source_metadata` | none found | Required source fields were present in the SQLite chunk mirror. |
| `missing_post_identity` | `sgf_phpbb_current:forum-5:thread-165192:chunk-0001` / Pedal Steel / `Derby  History` | `post_uids=[]`; source cards cannot identify contributing posts cleanly. |
| `mixed_topic_content` | `sgf_phpbb_current:forum-11:thread-100314:chunk-0001` / Electronics / `Standel S-80 head` | Multi-post chunk includes question, links, answers, and duplication. |

## Recommended Cleanup Rules

Phase 3B cleaner/classifier should:

- Remove standalone and inline forum navigation artifacts, especially `Top`, `Back to top`, edit notices, and attachment permission text.
- Detect `Top`-based body duplication and keep one copy of the post body.
- Strip raw `sp=sharing` and similar share fragments from embed text while keeping normalized links in metadata.
- Split link-only rows into metadata-only records or exclude them from answer embeddings unless they contain explanatory context.
- Redact or remove raw email/contact blocks from embed text and source-card excerpts.
- Move signature separators, gear-list footers, URLs, and repeated rig tails into metadata such as `signature_text`.
- Drop quote-only posts and reduce nested quote blocks before chunking.
- Pair question posts with nearby answer/advice posts when possible; avoid standalone question-only chunks.
- Classify sale/wanted/chatter/event/memorial content before chunking so retrieval can filter or down-rank it.
- Add explicit `post_role`, `chunk_role`, `answer_density`, `noise_score`, `source_metadata_complete`, and `entity_match` fields.
- Preserve raw corpus inputs exactly and write all derived v2 output under `corpus-v2/`.

## Risk Assessment

Likely answer-quality risks:

- `Top` duplication and repeated body text, because they appear in source cards and can leak into answers.
- Quote-heavy chunks, because they make attribution and answer grounding messy.
- Question-only and link-only chunks, because they retrieve plausible topics without giving the model enough evidence.
- Email/contact blocks, because they create privacy and source-card cleanliness risk.
- Oversized and mixed-topic chunks, because they dilute retrieval relevance and can support the wrong answer.
- Missing post identity, because source cards lose traceability to specific posts.

Harmless or tolerable if classified:

- Many `junk_phrase` issue rows are false positives when words like `thanks`, `sold`, or `bump` appear inside otherwise substantive chunks.
- `answer_advice_like_chunks` are mostly valuable, but need cleanup around their edges.
- Some event and memorial content is valid corpus content if the user asks about organizations, history, or people; it should be isolated by role rather than blindly deleted.
- Gear signatures can be useful for player/rig questions if stored separately from answer text.

Requires rebuild and re-embedding to fix:

- Any removal of `Top`, duplicated post body, quote blocks, contact blocks, or signature text from embedded text.
- Any chunk regrouping, especially question-plus-answer pairing and oversized chunk splitting.
- Any role-aware filtering of sale/wanted/chatter, event, memorial, link-only, or question-only chunks at embedding time.
- Any metadata change that should exist inside v2 Chroma, including scalar post identity, `chunk_role`, `post_role`, and quality scores.

Does not require rebuild and re-embedding:

- Updating this profile document.
- Additional read-only profiling or manual review.
- Runtime filtering experiments that only inspect current metadata, as long as app/backend behavior is not changed.

## Recommended Phase 3B Implementation Prompt

```text
Begin Phase 3B cleaner/classifier for The Turnaround corpus_v2.

This is YELLOW. Stop after presenting the implementation plan and proposed diff unless explicitly approved to apply it.

Use docs/phase-3-corpus-cleanup-plan.md and docs/phase-3a-corpus-profile.md.

Do not modify v1 Chroma, reset Chroma, regenerate embeddings, delete corpus files, run live SGF scraping, overwrite corpus-unified/chunks.jsonl, change backend answer code, or change frontend code.

Design and implement a cleaner/classifier that reads existing current/legacy clean posts from:
- /Users/cory/Documents/sgf-scrape-test/corpus-clean/current-phpbb/clean_posts.jsonl
- /Users/cory/Documents/sgf-scrape-test/corpus-clean/legacy-ubb/clean_posts.jsonl

Target output paths only under corpus-v2/:
- corpus-v2/clean_corpus.jsonl
- corpus-v2/reports/cleaner-classifier-report.md
- corpus-v2/reports/samples/

Cleaner/classifier requirements:
- remove forum boilerplate and Top duplication from derived v2 text
- strip sp=sharing/share fragments from derived embed text
- classify or isolate signatures, gear-list signatures, contact blocks, quote blocks, link-only posts, sales/wanted/chatter, event, and memorial content
- assign post_role with the approved labels
- compute answer_density, noise_score, source_metadata_complete, entity_match, and thread_category
- preserve raw corpus files exactly
- include focused tests for each cleanup rule

Do not chunk or embed yet. End with files changed, tests run, risks, human decision needed, recommended next step, and explicit confirmation that v1 Chroma was not modified.
```

## Commands Run

All commands were read-only except creating this Markdown report.

- `sed -n '1,220p' docs/phase-3-corpus-cleanup-plan.md`
- `git status --short`
- `test -f .../chunks.jsonl && test -f .../unified_chunk_issues.tsv && test -f .../unified_corpus.sqlite`
- Read-only Python profiling attempts against `chunks.jsonl`; these were stopped because full regex scans over the 1.7GB JSONL were too slow.
- Read-only SQLite aggregate queries against `file:/Users/cory/Documents/sgf-scrape-test/corpus-unified/unified_corpus.sqlite?mode=ro`
- `awk -F '\t'` count of `/Users/cory/Documents/sgf-scrape-test/corpus-unified/reports/unified_chunk_issues.tsv`
- Read-only SQLite sample queries for representative chunks.
- `git diff --check -- docs/phase-3a-corpus-profile.md`
- `ps ...` checks to confirm no profiling process was left running.

## Current V1 Chroma Statement

The current v1 Chroma store was not modified. This Phase 3A work did not reset Chroma, regenerate embeddings, delete corpus files, run live SGF scraping, overwrite `corpus-unified/chunks.jsonl`, or change backend/frontend code.
