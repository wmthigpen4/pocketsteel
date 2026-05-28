# Phase 3E Normalized Claims Plan

Scope: define a future normalized-claim layer for The Turnaround. This layer is separate from corpus-v2 evidence chunks and must not replace source-faithful retrieval chunks.

Task mode: GREEN for this planning document. Implementing claim extraction, writing claim artifacts, changing retrieval, or changing answer behavior requires explicit approval.

## Purpose

Forum evidence chunks preserve what people actually wrote. Normalized claims would sit beside those chunks as a derived, reviewable layer that summarizes repeated advice, tradeoffs, and facts in cleaner language while keeping provenance back to source chunks and posts.

This distinction matters:

- Evidence chunks stay source-faithful and quote/source-card friendly.
- Normalized claims are compact statements used for synthesis, deduplication, contradiction tracking, and review.
- Claims must never hide uncertainty, anecdotal status, conflicts, or weak sourcing.
- Claims must keep enough provenance to show the exact forum evidence behind the summary.

## Proposed Outputs

Potential future paths, subject to approval:

- `corpus-v2/claims/normalized_claims.jsonl`
- `corpus-v2/claims/claim_evidence_links.jsonl`
- `corpus-v2/reports/normalized-claims-audit.md`

These files should be generated only after corpus-v2 chunks pass preflight and only into ignored derived-output locations.

## Claim Record Shape

Suggested fields:

- `claim_id`: stable deterministic ID from normalized text plus evidence IDs.
- `claim_text`: concise normalized statement.
- `claim_type`: controlled type label.
- `confidence`: controlled confidence label.
- `topic_entities`: instruments, brands, players, organizations, parts, techniques, tunings, or event names.
- `caveats`: limits, exceptions, model-specific details, or safety warnings.
- `support_count`: number of supporting evidence chunks/posts.
- `conflict_count`: number of conflicting evidence chunks/posts.
- `evidence_chunk_ids`: chunk-v2 IDs that support the claim.
- `source_urls`: source URLs for review/source cards.
- `post_uids`: post IDs contributing evidence.
- `source_quote_snippets`: short snippets for audit, not long copied passages.
- `created_by`: extractor version or manual-curation marker.
- `review_status`: `unreviewed`, `reviewed`, `rejected`, or `needs_more_evidence`.

## Claim Types

Initial `claim_type` values:

- `user_experience`: a person reports what they bought, tried, heard, used, liked, disliked, or observed.
- `setup_tradeoff`: a configuration choice with practical upside/downside, for example string gauge, wound/plain string, pickup height, amp setting, or copedent change.
- `maintenance_guidance`: care, cleaning, lubrication, electronics repair, adjustment, storage, or safety guidance.
- `technique_guidance`: picking, blocking, bar movement, volume pedal technique, intonation, practice, or learning guidance.
- `brand_comparison`: comparison between makers, models, pickups, amps, speakers, seats, pedals, or accessories.
- `vendor_guidance`: advice about builders, repairers, vendors, parts sources, support channels, or availability.
- `player_bio_fact`: factual statement about a player, recording, band, role, instrument, tuning, or career detail.
- `organization_fact`: factual statement about clubs, conventions, associations, events, publications, archives, or institutions.

Questions, jokes, classifieds, raw contact blocks, and unsupported speculation should not become claims by default.

## Confidence Labels

Initial `confidence` values:

- `curated_high`: human-reviewed, well-supported, and safe to present as a stable fact or guidance.
- `source_supported`: supported by one or more credible source chunks, but not manually elevated to curated status.
- `anecdotal`: based mainly on personal experience, preference, or a single user's report.
- `conflicting`: multiple source chunks disagree or recommend different actions.
- `weak_source`: low evidence count, noisy source text, unclear attribution, or uncertain entity matching.

Confidence is not the same as truth. It describes evidence quality and agreement.

## Extraction Rules

Only extract claims from chunks that are clean enough for synthesis:

- Prefer `chunk_role=answer_advice` with acceptable `noise_score`.
- Allow `opinion` only when claim text clearly says it is subjective.
- Allow `event`, `memorial`, `player_bio_fact`, and `organization_fact` only for factual historical or organizational claims.
- Do not extract from `question` unless paired evidence answers it.
- Do not extract from `sale_wanted`, `contact_block`, `gear_signature`, `link_only`, or `joke_chatter`.
- Do not extract from `mixed_topic_quarantined` chunks without human review.

Every claim should preserve provenance:

- At least one `evidence_chunk_id`.
- At least one `source_url`.
- One or more `post_uids` when available.
- Enough metadata to reconstruct thread title, forum, and source-card context.

## Examples

### Wound 6th String Tradeoff

Forum-style language:

```text
I tried a wound 6th on E9. It felt smoother and helped the lower, but I had to adjust the pull and it was not as snappy as a plain string.
```

Normalized claim:

```json
{
  "claim_type": "setup_tradeoff",
  "claim_text": "A wound 6th string on E9 can feel smoother and improve lowering behavior, but it may require pull adjustment and can feel less snappy than a plain string.",
  "confidence": "anecdotal",
  "caveats": ["Based on user experience; guitar setup and changer behavior may vary."]
}
```

If multiple independent posts support the same tradeoff, confidence could become `source_supported`. If posts disagree, mark `conflicting`.

### Sewing Machine Oil Maintenance Guidance

Forum-style language:

```text
I use sewing machine oil on the changer, just a tiny drop. Don't flood it or it will collect dirt.
```

Normalized claim:

```json
{
  "claim_type": "maintenance_guidance",
  "claim_text": "Some players use a tiny amount of sewing machine oil on changer parts, with the caveat that excess oil can attract dirt.",
  "confidence": "source_supported",
  "caveats": ["Use sparingly.", "Check manufacturer guidance for the specific guitar."]
}
```

The normalized claim should avoid presenting this as universal maintenance law unless curated evidence supports that wording.

### Purchase Experience, Not Universal Recommendation

Forum-style language:

```text
I bought Brand X's seat and liked it. It was comfortable on long gigs.
```

Normalized claim:

```json
{
  "claim_type": "user_experience",
  "claim_text": "One user reported liking a Brand X seat and finding it comfortable on long gigs.",
  "confidence": "anecdotal",
  "caveats": ["User experience, not a universal recommendation."]
}
```

This should not become: `Brand X seats are the best choice for long gigs.`

### Question, Not A Claim

Forum-style language:

```text
Has anyone compared Brand A and Brand B pickups in a push-pull?
```

Normalized claim:

```json
{
  "claim_type": null,
  "claim_text": null,
  "confidence": null,
  "extraction_decision": "question_not_claim"
}
```

A question can link to later answer evidence, but the question itself is not a normalized claim.

## Conflict Handling

Claims should make disagreement visible:

- Merge near-duplicate claims only when the normalized meaning is materially the same.
- Keep competing claims separate when advice conflicts.
- Use `conflicting` confidence when evidence supports incompatible recommendations.
- Store conflict links, for example `conflicts_with_claim_ids`.
- Prefer wording that names the condition: "for some guitars", "on this model", "in one user's setup", or "when the symptom is..."

## Review Workflow

Suggested future workflow:

1. Extract candidate claims from reviewed corpus-v2 chunks.
2. Cluster near-duplicates by topic entities and normalized text.
3. Attach provenance and confidence.
4. Produce an audit report with samples by claim type and confidence.
5. Human-review high-impact claims before answer integration.
6. Use claims only as synthesis aids while still grounding answers in evidence chunks.

## Non-Goals

- Do not replace evidence chunks.
- Do not summarize away attribution.
- Do not create claims from questions alone.
- Do not turn anecdotes into universal advice.
- Do not use normalized claims to bypass source-card display.
- Do not change backend answer code or retrieval behavior as part of this plan.

## Approval Gate

Before implementing normalized claims, the user should approve:

- Claim schema.
- Output paths.
- Extraction thresholds.
- Confidence label behavior.
- Human review requirements.
- Whether claims are only offline audit artifacts or can later participate in answer generation.

## Current V1 Chroma Statement

This planning document does not modify v1 Chroma, run embeddings, delete corpus files, run live SGF scraping, overwrite `corpus-unified/chunks.jsonl`, change backend answer code, change frontend code, or switch app config.
