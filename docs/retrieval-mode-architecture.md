# Retrieval Mode Architecture

The Turnaround should choose its answer evidence deliberately. Stable steel-guitar facts, current vendor links, historical forum wisdom, future private material, and fallback guardrails are different source lanes with different risk profiles. This document defines the retrieval modes and the intended decision flow before broader behavior changes are implemented.

This is an architecture document only. It does not recommend switching production behavior immediately.

## Goals

- Make source choice explicit before answer synthesis.
- Keep stable rules separate from retrieved forum text.
- Keep curated current links separate from SGF/RAG evidence.
- Prepare for private lessons, manuals, transcripts, and personal source material without mixing them into public answers by accident.
- Give answer contracts enough context to decide what must be answered directly, what must be cited, and when to fall back.

## Retrieval Modes

The hybrid retrieval scaffold uses these concrete mode names:

- `sgf_only`
- `private_only`
- `hybrid_private_first`
- `hybrid_sgf_first`
- `rules_only`
- `curated_only`

Default behavior must remain `sgf_only` with private sources disabled.

### `rules_only`

Use deterministic steel-guitar rules and theory facts without relying on retrieval.

Primary use cases:

- E9 open string notes
- common Emmons pedal/lever changes
- basic theory such as triads, intervals, and Nashville numbers
- stable copedent/fretboard relationships such as A+F and common grips

Examples:

- `What is a triad?`
- `What does A+F do?`
- `How do I play a 2m in G?`
- `What gauge is the 10th string on E9?`

### `curated_only`

Use human-reviewed curated sources for current or official links. Curated sources are not RAG evidence; they are maintained references for answers that need current public starting points.

Primary use cases:

- vendors and buying guidance
- official organizations or events
- official brand references
- lessons/reference links
- classifieds or used-market starting points

Examples:

- `Where can I buy a slide bar?`
- `What is TSGA?`
- `Who makes pack-a-seats?`

### `sgf_rag` / `sgf_only`

Use retrieved and reranked Steel Guitar Forum chunks as evidence for forum wisdom, historical discussion, practical experience, and source cards.

Primary use cases:

- tone/gear experience
- troubleshooting reports
- player history when source quality is strong
- builder/mechanical discussion
- practical playing advice from forum threads

Examples:

- `Why would a player prefer a wound sixth string?`
- `What are common Fender Steel King settings?`
- `How do players use the 9th string?`

### `private_sources` / `private_only`

Future mode for user-authorized private lessons, manuals, transcripts, and personal documents. This should not be active for public users until access control, provenance, and ingestion policy are explicit.

Primary use cases:

- private lesson transcript lookup
- user-uploaded manual/reference search
- personal practice notes
- paid or member-only material when allowed by rights and user authorization

Private sources must never be returned to users who do not have access to that source material.

### `hybrid`

Use more than one source lane when the intent requires it.

Common combinations:

- rules layer leads, SGF RAG supports with source cards
- curated links lead, SGF RAG provides historical context
- private source answer leads, public SGF/curated sources supplement if allowed
- answer contract requires direct rules answer plus retrieved examples

For SGF v2 plus private sources, use one of two explicit hybrid modes:

- `hybrid_private_first`: search private sources first, then SGF v2.
- `hybrid_sgf_first`: search SGF v2 first, then private sources.

Examples:

- `What does A+F do?` can use `rules_only` for the answer and `sgf_rag` for source cards.
- `Where can I buy a slide bar?` can use `curated_only` for current links and `sgf_rag` only as historical background if clean.

### `no_source_fallback`

Use when no appropriate evidence lane can answer confidently.

Primary use cases:

- weak retrieval
- source mismatch
- current roster not available
- sensitive identity speculation
- copyright/song guardrail
- missing context

The fallback should be direct and user-facing. It should not mention internal terms such as corpus, source cards, distillation, or implementation details.

## Intent Routing

Intent routing should choose a retrieval mode before answer composition.

| Intent shape | Preferred mode | Notes |
| --- | --- | --- |
| Basic theory/copedent/fretboard | `rules_only` or `hybrid` | Check `steel_rules.py` first. RAG should not override stable theory. |
| Buying/current/vendor | `curated_only` or `hybrid` | Use curated source registry for current links. Avoid stale forum claims. |
| Forum wisdom and lived experience | `sgf_rag` | Use reranked SGF chunks as evidence. Keep raw excerpts out of answer prose unless clean and intentional. |
| Private lesson/manual/transcript | `private_sources` or `hybrid` | Future mode gated by source visibility and user authorization. |
| Current roster/current employment | `no_source_fallback` or curated official source | Avoid stale forum claims. Point to official tour/session credits when current evidence is absent. |
| Sensitive identity | `no_source_fallback` | Do not speculate about private identity traits. |
| Song/tab requests | `rules_only`, `hybrid`, or `no_source_fallback` | Follow song-learning guardrails: discussion and original exercises are allowed; full copyrighted tab/lyrics are not provided by default. |

The routing order should be conservative:

1. Safety and policy checks.
2. Stable rules check for theory/copedent facts.
3. Curated source check for current/official/vendor questions.
4. User-authorized private source check when implemented.
5. SGF RAG retrieval for forum wisdom.
6. Fallback guardrails if sources are weak, stale, mismatched, or unavailable.

## Source Priority

The answer engine should treat source lanes by their strengths:

1. `steel_rules.py` for stable E9, copedent, and theory facts.
2. Curated sources for current/official links, vendors, organizations, and trusted public references.
3. Private source corpus when the user is authorized and the material is allowed for that use.
4. SGF RAG for historical forum wisdom, player experience, troubleshooting, and discussion-backed answers.
5. Fallback when source support is weak or unavailable.

This priority is not a trust ranking for every claim. It is a routing model. SGF RAG can be excellent for lived experience, while curated sources are better for current links, and rules are better for stable theory.

## Visibility And Access

Retrieval mode must respect who is asking and what sources are allowed.

| Audience | Allowed source lanes | Notes |
| --- | --- | --- |
| Public/anonymous | rules, curated public sources, approved public SGF RAG | No private lessons, personal notes, paid transcripts, or admin-only metadata. |
| Beta/private preview | rules, curated public sources, approved SGF RAG, beta-enabled private sources if authorized | Access is still explicit per source. |
| Future paid users | same as beta plus licensed/paid sources when contractually allowed | Payment does not imply redistribution or quote rights. |
| Admin | inspection and debugging access based on admin tooling | Admin views may expose mode/debug metadata that normal users should not see. |
| Private/personal material | only owner-authorized source retrieval | Must not leak into public answers or shared source cards. |
| Public SGF material | available to public/beta answers if cleaned and allowed | Preserve source URL and metadata. |

## Hybrid SGF v2 And Private Source Scaffold

Known source stores:

| Lane | Path | Collection |
| --- | --- | --- |
| SGF v2 | `corpus-v2/vector-stores/chroma` | `steel_guitar_unified_v2` |
| Private source-inbox | `corpus-private/vector-stores/chroma` | `steel_guitar_private_sources_v1` |

Proposed environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `STEEL_RAG_RETRIEVAL_MODE` | `sgf_only` | Requested retrieval mode. |
| `STEEL_RAG_ENABLE_PRIVATE_SOURCES` | unset/false | Required feature flag before any private retrieval can run. |
| `STEEL_RAG_SGF_V2_CHROMA_PATH` | `corpus-v2/vector-stores/chroma` | SGF v2 vector path. |
| `STEEL_RAG_SGF_V2_COLLECTION` | `steel_guitar_unified_v2` | SGF v2 collection. |
| `STEEL_RAG_PRIVATE_CHROMA_PATH` | `corpus-private/vector-stores/chroma` | Private source vector path. |
| `STEEL_RAG_PRIVATE_CHROMA_COLLECTION` | `steel_guitar_private_sources_v1` | Private source collection. |
| `STEEL_RAG_RETRIEVAL_DEBUG` | unset/false | Allows admin/dev-only retrieval metadata inspection. |

Access rules:

- Public/anonymous users must never use private sources.
- Beta/private preview users may use private sources only when `STEEL_RAG_ENABLE_PRIVATE_SOURCES=true`.
- Admin/dev users may inspect retrieval mode metadata only when debug mode is explicitly enabled.
- Future paid/free tier access must be explicit; payment status alone should not imply private-source rights.

Current scaffold behavior:

- The default plan is `sgf_only`.
- Private retrieval is disabled by default, even for beta users.
- If a private or hybrid mode is requested without private access, the plan falls back to `sgf_only`.
- `/api/search` can use the retrieval plan when explicitly configured.
- `/api/answer` does not use private retrieval yet.
- Private search results are never returned to anonymous/public callers.
- Retrieval debug metadata is only returned when `STEEL_RAG_RETRIEVAL_DEBUG=true` and the caller is admin/dev.

## Metadata Requirements

Every retrievable or curated source should preserve metadata needed for routing, access, provenance, and answer display.

Required or strongly preferred fields:

- `source_system`
- `visibility`
- `source_type`
- `provenance_status`
- `redistribution_allowed`
- `embedding_allowed`
- `answer_quote_allowed`
- `source_url`
- `author`
- `title`
- `date`
- `forum_name` or equivalent source collection name
- `thread_url` for SGF-derived material
- `source_owner` for private/personal material when applicable
- `last_reviewed` for curated sources

These fields support two separate decisions:

- Can the system retrieve and use this material?
- Can the system show, quote, cite, or redistribute this material in an answer?

## Answer Contract Interaction

Retrieval modes feed answer contracts. The contract decides what the final answer must contain and what source material may appear in answer prose.

### `player_bio`

Preferred modes:

- `rules_only` for curated known entity facts when available
- `sgf_rag` for historical support
- `no_source_fallback` when only weak mentions exist

Contract requirements:

- direct first sentence
- why the player matters
- style, contribution, or association when supported
- no tiny mention fragments or birthday/forum chatter

### `copedent_fretboard`

Preferred modes:

- `rules_only`
- `hybrid` with SGF support

Contract requirements:

- what changes
- interval or chord result
- fret/string/pedal example
- practical use

### `diagnostic_troubleshooting`

Preferred modes:

- `sgf_rag` for real-world reports
- `hybrid` with rules/general safety guidance

Contract requirements:

- likely causes
- diagnostic path
- safety note when electrical or mechanical risk exists
- no copied forum questions as the answer

### `vendor_buying_guidance`

Preferred modes:

- `curated_only`
- `hybrid` only when SGF context is clean and non-stale

Contract requirements:

- curated sources when available
- what to choose
- current availability caveat
- no random old forum vendor links or private email recommendations

### `brand_comparison`

Preferred modes:

- `hybrid`
- `sgf_rag` for lived experience
- curated official sources only if the user asks where to buy or verify current brand status

Contract requirements:

- compare both brands
- no universal winner unless strongly source-backed
- include condition, setup, mechanics, support, tone, weight, copedent fit, and budget where relevant
- no vendor links unless asked

### `song_learning`

Preferred modes:

- `rules_only` for theory/position strategy
- `hybrid` for style/forum context
- `no_source_fallback` for broad or copyrighted-tab requests

Contract requirements:

- song discussion, style, harmony, technique, tone, and arrangement approach are allowed
- original exercises and public-domain examples are allowed
- full copyrighted lyrics, full copyrighted tab, and complete note-for-note copyrighted arrangements are not provided by default
- ask for song/key/tuning when missing

### `current_roster`

Preferred modes:

- curated official source if available
- `no_source_fallback` if not

Contract requirements:

- if not current/source-backed, say so plainly
- recommend official tour credits, album/session credits, or current band listings
- do not treat old forum mentions as current roster facts

### `sensitive_identity`

Preferred mode:

- `no_source_fallback`

Contract requirements:

- do not speculate about private identity traits
- answer respectfully and briefly
- do not pull forum snippets

### `fallback_unknown`

Preferred mode:

- `no_source_fallback`

Contract requirements:

- no internal implementation language
- no raw source fragments
- say the information is not available with enough confidence
- offer one useful next step

## Failure Handling

### Weak Retrieval

If retrieval finds only noisy, mention-only, or question-fragment chunks, the answer should not paste those fragments. Use a short general answer when the intent is recognizable, or fallback if not.

### No Sources

If no lane can answer, say so directly and ask for one useful narrowing detail. Avoid internal wording such as corpus or source cards.

### Stale Source Risk

Current status, vendor inventory, rosters, active companies, and event details should not rely on old forum posts. Prefer curated official links or fallback to official current references.

### Source Mismatch

If the question asks about one entity and retrieved sources discuss another, do not synthesize a false answer. Preserve source cards if useful, but warn or fallback in the answer body.

### Private-Source Access Denied

If a user asks about private material they are not authorized to use, do not reveal that source content exists. Provide a generic access-limited answer or ask them to provide the material in the current session.

### Current Info Not Available

For current rosters, tour personnel, business status, or fresh event details, say current information is not available from the information at hand and point to official credits/listings.

### Copyright/Song Guardrail

Do not refuse song discussion broadly. Explain style, approach, chord movement, practice strategy, and original exercises. Do not provide full copyrighted lyrics, full copyrighted tab, or complete note-for-note copyrighted arrangements by default.

## Implementation Plan

### Phase 1: Document And Add Mode Enum Only

- Add a small retrieval mode enum or constants.
- Do not change answer behavior broadly.
- Add tests that the enum values exist.
- Use this document as the design reference.

### Phase 2: Route Rules, Curated, And SGF Modes Explicitly

- Make intent routing choose an explicit retrieval mode.
- Keep existing answer quality behavior unless tests show safe improvements.
- Add admin/dev-only logging for selected mode and reason.

### Phase 3: Add Private Source Retrieval

- Define private source metadata and access checks.
- Require source visibility and user authorization checks before retrieval.
- Keep private source cards separate from public SGF source cards.
- Do not mix private and public sources unless the answer mode and user access allow it.

### Phase 4: Add Answer Eval Per Mode

- Extend the answer eval question bank with expected mode or expected contract.
- Track failures by mode: rules, curated, SGF RAG, private, hybrid, fallback.
- Add tests for mode leakage, stale source misuse, and private-source access denial.

### Phase 5: Expose Mode/Debug Metadata Only To Admin/Dev

- Normal users should see direct answers and source cards, not internal retrieval mode diagnostics.
- Admin/dev users may see mode, contract, confidence, source-lane choices, and fallback reasons for debugging.
- Do not expose private-source availability or access-denied details to unauthorized users.

## Non-Goals For This Step

- Do not deploy.
- Do not change DNS or Cloudflare routing.
- Do not modify Chroma, embeddings, or vector indexes.
- Do not run scraping.
- Do not ingest source-inbox material.
- Do not switch app behavior immediately except for tiny, separately tested changes.

## Open Risks

- Private source ingestion needs clear provenance and access policy before implementation.
- Curated source freshness depends on human review.
- SGF RAG is historically useful but can be stale for current status questions.
- Hybrid answers need strict source provenance so the UI can show what came from rules, curated links, private sources, and SGF.
- Debug metadata could leak sensitive source availability if exposed to normal users.

## Recommended Next Step

Implement Phase 1 only: add retrieval mode constants or an enum, add minimal tests, and leave answer behavior unchanged. That gives future work a stable vocabulary without moving the app into a new routing regime prematurely.
