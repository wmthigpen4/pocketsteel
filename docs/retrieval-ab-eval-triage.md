# Retrieval A/B Eval Triage

Task mode: GREEN read-only analysis and documentation. This triage did not modify v1 Chroma, modify v2 Chroma, reset Chroma, regenerate embeddings, switch app config, deploy, change DNS, or expose anything publicly.

## Inputs

- A/B markdown report: `corpus-v2/reports/retrieval-ab-eval-v1-v2.md`
- A/B JSON report: `corpus-v2/reports/retrieval-ab-eval-v1-v2.json`
- Phase 3D preflight markdown: `corpus-v2/reports/phase3d-full-preflight-report.md`
- Phase 3D preflight JSON: `corpus-v2/reports/phase3d-full-preflight.json`
- Read-only v2 Chroma metadata sample: `corpus-v2/vector-stores/chroma`, collection `steel_guitar_unified_v2`

## Readiness Decision

V2 is not ready for an app switch.

V2 is a strong cleanup win, but current retrieval behavior is not yet strong enough for private-preview answers. It greatly reduces leakage, keeps source URLs and post identity intact, and scores slightly higher overall, but it also returns too many short mention fragments, has a higher duplicate-thread rate, and currently hides useful v2 metadata from the retrieval normalizer/reporting layer.

The smallest safe next step is to fix retrieval/source-card normalization and reranking without rebuilding or re-embedding first.

## Top-Level Comparison

| Metric | v1 | v2 | Triage |
| --- | ---: | ---: | --- |
| Questions | 191 | 191 | Same question bank |
| Retrieved sources | 955 | 955 | Same topK=5 run |
| Zero-source questions | 0 | 0 | No coverage collapse |
| Source URL rate | 100.00% | 100.00% | Good |
| Excerpt leakage rate | 41.68% | 2.09% | Major v2 win |
| Duplicate source rate | 12.67% | 15.18% | v2 regression |
| Metadata completeness | 89.32% | 54.55% | Evaluator alias mismatch, not an embed-time source metadata loss |
| Post identity completeness | 94.17% | 100.00% | v2 win |
| Score min | 0.484769 | 0.485710 | Similar floor |
| Score median | 0.600403 | 0.617826 | v2 slightly higher |
| Score mean | 0.594729 | 0.612196 | v2 slightly higher |
| Score max | 0.707975 | 0.745232 | v2 higher |

Forum coverage changed in the retrieved set:

- v1: Band-in-a-Box, Electronics, New Product Announcements, No Peddlers, Pedal Steel, Recording, Slide Guitar and String Bender Guitars, Steel Players, Steel Without Pedals, Steel on the Web, Tablature.
- v2: Band-in-a-Box, Builders' Corner, Electronics, No Peddlers, Pedal Steel, Steel Players, Steel Without Pedals, Steel on the Web, Tablature.
- Both sides: `sgf_phpbb_current`, `sgf_ubb_legacy`.

This does not prove v2 lacks the missing forums globally; it only shows they did not appear in this topK retrieval run.

## Metadata Completeness Mismatch

The A/B evaluator scores metadata completeness using normalized v1-style fields:

```text
source_system, forum_name, thread_title, thread_url, chunk_id, source_kind,
forum_id, thread_id, legacy_thread_uid, thread_category, chunk_index
```

The v2 preflight defines source metadata completeness differently:

```text
chunk_id, source_system, forum_name, thread_id, thread_title, chunk_text,
chunk_role, source_url/thread_url
```

A read-only sample of v2 Chroma metadata showed these keys:

```text
chunk_id, chunk_role, chunk_text, cleanup_flags, forum_name, noise_score,
post_role_summary, post_uids, quality_score, source_metadata_complete,
source_system, source_url, text, thread_id, thread_title, thread_url
```

The retrieved v2 rows are missing the evaluator's v1-era fields:

| Evaluator field | v2 missing count | Notes |
| --- | ---: | --- |
| `source_kind` | 955/955 | Can be derived as a source-card alias, e.g. `forum_thread_chunk` or `chunk_role`-backed |
| `forum_id` | 955/955 | Not present in v2 metadata |
| `legacy_thread_uid` | 955/955 | Not present in v2 metadata |
| `thread_category` | 955/955 | Not present in v2 metadata |
| `chunk_index` | 955/955 | Not present as a field; can be parsed from v2 chunk IDs if needed |

Conclusion: the 54.55% v2 metadata completeness result is primarily an evaluator/source-card alias mismatch. Phase 3D preflight reported `717425/717425` source metadata completeness and `717425/717425` post identity completeness, and sampled Chroma rows include `source_metadata_complete=True`. Re-embedding is not needed to fix this specific reporting/source-card issue.

## Category Weaknesses

| Category | v2 signs of weakness | Suggested safe fix |
| --- | --- | --- |
| Player biography | 24 short sources in 75; examples return mention fragments such as "likes Buddy Emmmons." | Downrank mention-only fragments; boost `Steel Players`; prefer longer excerpts with person-name density and biographical verbs |
| Subjective ranking | 23 short sources in 50; 10 question-like sources; some results retrieve meta chatter about players | Downrank question-only chunks; boost list/history threads; require minimum useful length unless score is very high |
| Copedent/fretboard | 33 short sources in 100; several fragments mention positions without instruction context | Minimum excerpt length; boost Tablature/Pedal Steel instructional threads; downrank isolated positional fragments |
| Gear/tone | 12 short sources in 100; 8 question-like sources; leakage much improved | Downrank question-only chunks; use `quality_score` and `noise_score`; preserve high-quality gear advice |
| Maintenance/troubleshooting | 11 short sources in 75; generally cleaner and higher median score, but still has isolated fragments | Apply minimum text length and role/noise filters; keep safety-sensitive questions on stronger answer/advice chunks |

Retrieved v2 role distribution for the 955 returned sources:

| Role | Count |
| --- | ---: |
| `answer_advice` | 859 |
| `question` | 39 |
| `unknown` | 22 |
| `opinion` | 15 |
| `event` | 15 |
| `memorial` | 5 |

The role distribution is mostly sane, but the presence of `question`, `unknown`, `event`, and `memorial` in topK results can hurt answer quality for many user intents unless retrieval filters or reranks by intent.

## Review Samples

### 10 V2 Wins

These are mostly cleanliness wins, not automatic answer-quality wins.

| ID | Category | Why it wins | V2 first source |
| --- | --- | --- | --- |
| F008 | maintenance_parts_safety | v1 had 5 leaking excerpts; v2 had 0 | `Cabinet Drop`: "of the corner welds. You talk about cabinet drop." |
| I005 | events_organizations | v1 had 5 leaking excerpts; v2 had 0 and retrieved Hall of Fame context | `Hall of Fame Full List?`: "Where can I find the most updated list of the Steel Guitar Hall of Fame? ..." |
| G011 | accessories_products | v1 had 4 leaking excerpts; v2 had 0 | `String choice`: stainless vs nickel discussion |
| B008 | rankings_subjective_players | v1 had 5 leaking excerpts; v2 had 1 | `Songs the band made you play that you despised`: player-selection discussion |
| A002 | entity_player_biography | v1 had 4 leaking excerpts; v2 had 0 | `Lloyd Green alert: Harper Simon interview`: "Lloyd Green is a hero to us all..." |
| C010 | e9_fretboard_copedent | v1 had 4 leaking excerpts; v2 had 0 and instructional chord context | `I need a C note...`: major/minor grips |
| I007 | events_organizations | v1 had 4 leaking excerpts; v2 had 0 | `New Member`: Steel Guitar Forum welcome/context |
| J010 | source_mismatch_no_source | v1 had 4 leaking excerpts; v2 had 0 | `Best steel seat?`: pack-a-seat discussion |
| B002 | rankings_subjective_players | v1 had 3 leaking excerpts; v2 had 0 and higher median score | `Vote for your favorite steel player`: named-player list |
| J005 | source_mismatch_no_source | v1 had 3 leaking excerpts; v2 had 0 and higher median score | `Push-Pull lowering G#'s to G or F#???`: pedal-change discussion |

### 10 V2 Losses

| ID | Category | Problem | V2 first source |
| --- | --- | --- | --- |
| D001 | practice_plan_questions | 5/5 v2 excerpts are short; first result is a question fragment | `practice area and routine`: "do you find time to pratice." |
| A004 | entity_player_biography | 5/5 v2 excerpts are short; mention-only biography evidence | `Day set-up`: "which is mostly Jimmy Day..." |
| B010 | rankings_subjective_players | 5/5 short; question-like fragment | `Arpeggios on E9th?`: "steel players -- true or not?" |
| N001 | technique_improvement | 5/5 short; not enough actionable technique context | `bigsby/clinesmith style blade PU vs. horseshoe`: "in less volume." |
| K008 | prompt_injection_hostile_retrieved_text | 5/5 short; irrelevant player mention | `Robert Randolf! is it just me or what!?`: "likes Buddy Emmmons." |
| D013 | practice_plan_questions | 5/5 short; too generic | `apartment living--how do you cope?`: "a practice tool." |
| C013 | e9_fretboard_copedent | 5/5 short; no instructional context | `Figuring out C6 songs on E9 neck`: "it's early E9." |
| C005 | e9_fretboard_copedent | 5/5 short; isolated position mention | `Is intonation easier with JI than with ET?`: "on that A+F position!" |
| K005 | prompt_injection_hostile_retrieved_text | 5/5 short; irrelevant source text | `Wh don't we play blues?`: "my opinions not creditable. [link removed]" |
| D010 | practice_plan_questions | 5/5 short; no practice plan substance | `"Can you play without sliding?"`: "the rehearsal schedule." |

### 10 Metadata Mismatch Examples

Each example has complete raw v2 source metadata but appears incomplete under the A/B evaluator because normalized fields are empty.

| ID | Missing normalized fields | Raw v2 fields present |
| --- | --- | --- |
| A001 | `source_kind`, `forum_id`, `legacy_thread_uid`, `thread_category`, `chunk_index` | `chunk_role`, `quality_score`, `noise_score`, `source_url`, `post_uids`, `source_metadata_complete` |
| A002 | Same | Same |
| A003 | Same | Same |
| A004 | Same | Same |
| A005 | Same | Same |
| A006 | Same | Same |
| A007 | Same | Same |
| A008 | Same | Same |
| A009 | Same | Same |
| A010 | Same | Same |

### 10 Too-Short Or Fragmentary Source Examples

| ID | Category | Length | Score | Role | Excerpt |
| --- | --- | ---: | ---: | --- | --- |
| H012 | brands_comparisons | 9 | 0.615132 | `answer_advice` | "as a D-10" |
| D012 | practice_plan_questions | 11 | 0.646396 | `answer_advice` | "to tune to." |
| K002 | prompt_injection_hostile_retrieved_text | 11 | 0.645516 | `answer_advice` | "to your PC." |
| G002 | accessories_products | 12 | 0.566212 | `answer_advice` | "bag or seat." |
| H012 | brands_comparisons | 13 | 0.632712 | `answer_advice` | "an SD10... SH" |
| C013 | e9_fretboard_copedent | 14 | 0.575849 | `answer_advice` | "it's early E9." |
| D002 | practice_plan_questions | 14 | 0.639051 | `answer_advice` | "it's early E9." |
| G014 | accessories_products | 14 | 0.648918 | `answer_advice` | "a pedal steel." |
| H004 | brands_comparisons | 14 | 0.607041 | `answer_advice` | "the Sho Bud..." |
| K010 | prompt_injection_hostile_retrieved_text | 14 | 0.608032 | `answer_advice` | "and it's over." |

### 10 Duplicate-Thread Examples

| ID | Category | Duplicate thread count | Thread |
| --- | --- | ---: | --- |
| J002 | source_mismatch_no_source | 3 | `Buddy Emmons, Look at THIS career!` |
| I006 | events_organizations | 3 | `Playing Steel with Keyboard Bass Pedals?` |
| M009 | targeted_directness_probes | 2 | `What to buy to buy Mullen G2 , MSA Legend` |
| M003 | targeted_directness_probes | 2 | `What to buy to buy Mullen G2 , MSA Legend` |
| L009 | latest_frontend_failures | 2 | `Tab for Panhandle Rag C6th` |
| L005 | latest_frontend_failures | 2 | `SHOJI: New Steel Guitar Brand from Japan` |
| L002 | latest_frontend_failures | 2 | `Leading church service with pedal steel` |
| L002 | latest_frontend_failures | 2 | `What to Play` |
| J003 | source_mismatch_no_source | 2 | `Sho Bud pros and cons?` |
| I010 | events_organizations | 2 | `Ntsga ?????` |

## Recommended Fixes Before Any Rebuild

1. Source-card metadata alias mapping:
   - Surface `chunk_role`, `quality_score`, `noise_score`, `source_metadata_complete`, `post_role_summary`, and `cleanup_flags` from v2 metadata into normalized retrieval results.
   - Treat `source_url` as an alias for `thread_url`; this already works.
   - Derive `source_kind` as `forum_thread_chunk` or a role-backed value.
   - Derive `chunk_index` from v2 chunk IDs where useful.
   - Stop treating absent v1-only fields such as `forum_id`, `legacy_thread_uid`, and `thread_category` as v2 metadata failures unless they are actually needed by source cards.

2. Minimum excerpt/text length filter:
   - Do not show or rank source excerpts shorter than a safe threshold, e.g. 80-120 characters, unless the row has exceptionally high score and strong metadata.
   - For answer generation, prefer a larger candidate pool, then filter/rerank before selecting topK.

3. `quality_score` and `noise_score` filter:
   - Downrank rows with high `noise_score`, especially above roughly 0.60.
   - Boost rows with strong `quality_score`, especially above roughly 0.70.
   - Use this as a rerank signal first, not as a hard global filter, because some historical/event sources may naturally score noisy.

4. Role-based retrieval filter or rerank:
   - For most answer intents, prefer `answer_advice`.
   - Downrank `question`, `unknown`, `event`, and `memorial` unless the question intent calls for them.
   - For player biographies, allow `memorial` or `event` only when the excerpt is long and biographical, not just a birthday or mention.

5. Per-thread dedupe:
   - Retrieve more than topK internally, then select no more than one source per `thread_url` until diversity is exhausted.
   - Keep the highest reranked source per thread.

6. Source-system/forum/category boosts:
   - Player biographies: boost `Steel Players`; downrank unrelated forums unless excerpt has strong biographical language.
   - Copedent/fretboard: boost `Tablature` and instructional `Pedal Steel` threads.
   - Gear/tone and maintenance: boost `Electronics`, `Pedal Steel`, and rows with advice-like role plus low noise.

7. Downrank question-only or mention-only fragments:
   - Detect excerpts ending in `?` or beginning with question words.
   - Downrank excerpts that contain only a name or gear term without verbs, dates, roles, comparisons, instructions, or enough surrounding context.

## Is Re-Embedding Needed?

Not yet.

The metadata mismatch does not require re-embedding. The fragment/duplicate issues might be addressable by retrieval normalization, filtering, and reranking over the existing v2 store. Re-embedding should be reserved for a later phase only if safer search/rerank changes still cannot recover strong source evidence from v2.

## What Must Pass Before V2 Powers Private Preview

- A rerun of the retrieval A/B report shows v2 leakage remains low while duplicate source rate is no worse than v1.
- Metadata completeness is measured against v2-aware aliases and source-card fields.
- Player biography samples return biographical evidence, not mention fragments.
- Copedent/fretboard and practice questions return instructional context, not isolated chord/position snippets.
- Maintenance and troubleshooting answers continue to avoid unsafe or under-supported advice.
- Answer eval against `/api/answer` passes at least as well as v1 after a separately approved v2 local config run.
- Human review approves a separate app-config switch plan. Until then, The Turnaround should remain on v1.

## Recommended Next Implementation Prompt

Implement a v2-aware read-only retrieval normalization and rerank pass without rebuilding embeddings or switching app config. Add aliases for v2 metadata (`chunk_role`, `quality_score`, `noise_score`, `post_uids`, `source_metadata_complete`, `cleanup_flags`), add a configurable minimum excerpt length filter, add per-thread dedupe after retrieving an expanded candidate pool, and add role/quality/noise rerank signals. Update tests and the retrieval A/B evaluator so v2 metadata completeness is scored against v2 aliases instead of v1-only fields. Do not modify either Chroma store, regenerate embeddings, or change answer quality logic.

## Current Chroma Statement

This triage used generated reports and a read-only sample of v2 Chroma metadata. It did not modify v1 Chroma, modify v2 Chroma, reset Chroma, regenerate embeddings, switch app config, deploy, change DNS, or expose anything publicly.
