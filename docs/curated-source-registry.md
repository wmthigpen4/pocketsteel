# Curated Source Registry

The curated source registry lives in `corpus_metadata/source_registry.json`.

Curated sources are human-reviewed links that The Turnaround may mention directly when an answer intent needs current or official reference material. They are separate from SGF/RAG evidence: RAG source cards show retrieved corpus material, while curated sources provide maintained links for things like vendors, official organizations, official brand pages, lessons/reference pages, and used-market starting points.

## When To Use Curated Sources

Use curated sources only when the answer intent calls for them:

- `vendor_buying_guidance`: buying paths, vendors, makers, stores, and selection cautions.
- `organization_event_lookup`: official organization and event pages.
- `official_brand_reference`: official brand or maker pages.
- `lessons_reference`: curated learning/reference pages.
- `classifieds_used_market`: used-market or classifieds starting points.

Do not inject curated links into unrelated answers. A copedent, technique, theory, or player-history answer should not randomly include vendor links just because the registry has them.

## Schema

Each object in `curated_sources` should include:

- `id`: stable lowercase identifier.
- `name`: user-facing source name.
- `url`: public URL.
- `category`: stable grouping such as `tone_bars`, `organization`, `brand_official`, `lessons_reference`, or `used_market`.
- `source_type`: source class such as `official`, `official/manufacturer`, `official_organization`, `dealer`, `forum/used_market`, or `curated_article_site`.
- `description`: concise explanation of why the source is useful.
- `caveat`: freshness, inventory, membership, compatibility, or verification warning.
- `last_reviewed`: `YYYY-MM-DD` date when a human last checked the entry.
- `active`: `true` only when the source may be shown.
- `allowed_answer_modes`: answer intents allowed to use the source.
- `tags`: small search/filter labels such as `tone_bars`, `vendor`, `official`, `events`, or `lessons`.

The old `curated_vendor_sources` block remains only for backward compatibility. New entries should go in `curated_sources`.

## Adding A Source

1. Add a JSON object to `curated_sources`.
2. Keep `description` factual and short.
3. Add a specific `caveat`; for vendors this usually means “check current availability.”
4. Set `allowed_answer_modes` narrowly.
5. Set `active` to `true` only after a human review.
6. Update `last_reviewed` when the URL or caveat is checked.
7. Add or update tests if the answer layer should use the new source.

Do not add private contact information, random forum links, dead links, paid-only sources, scraped posts, or one-off user emails as curated sources.

### Example Entry

Use this shape when adding a reviewed source:

```json
{
  "id": "example_steel_source",
  "name": "Example Steel Source",
  "url": "https://example.com/",
  "category": "tone_bars",
  "source_type": "official",
  "description": "Official page for an example steel-guitar accessory source.",
  "caveat": "Check current availability before recommending as in stock.",
  "last_reviewed": "2026-05-29",
  "active": false,
  "allowed_answer_modes": ["vendor_buying_guidance"],
  "tags": ["tone_bars", "vendor", "official"]
}
```

Required fields are `id`, `name`, `url`, `category`, `source_type`, `description`, `caveat`, `last_reviewed`, `active`, `allowed_answer_modes`, and `tags`. Keep `allowed_answer_modes` narrow so a vendor link does not appear in unrelated theory, technique, or player-history answers. New sources should start inactive until reviewed.

## Freshness Review

Review curated links periodically and whenever a user reports a stale result. On review:

- open the public URL manually,
- confirm it still represents the intended source,
- update `description` or `caveat` if the site changed,
- update `last_reviewed`,
- set `active` to `false` if the source is stale, misleading, or unavailable.

The answer layer filters inactive sources, so setting `active: false` is the safe way to retire a curated link without deleting the audit trail.

## Why Separate From SGF/RAG Evidence

Retrieved SGF chunks are historical evidence from forum discussions. They are useful for wisdom, context, and citations, but old vendor links and forum comments can be stale. Curated sources are maintained answer-time references for current links and trusted public pages. Keeping the layers separate lets answers say “check current availability” without pretending that an old forum thread proves current inventory or current status.
