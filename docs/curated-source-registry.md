# Curated Source Registry

The curated source registry lives in `corpus_metadata/source_registry.json`.

Use `curated_vendor_sources` for current, human-reviewed vendor and buying links that the answer layer may mention directly. These records are separate from retrieved forum evidence because old forum links can be stale, private, or incidental. The answer body may use curated vendor records for practical buying guidance while source cards continue to show retrieved RAG evidence.

## Adding a Vendor

Add a JSON object to `curated_vendor_sources` with:

- `name`: user-facing vendor/source name.
- `url`: public URL to send users to.
- `category`: stable grouping such as `tone_bars`, `steel_guitar_accessories`, or `used_market`.
- `short_description`: one concise sentence explaining why the source is useful.
- `caveat`: inventory, membership, compatibility, or verification caveat.
- `last_reviewed`: `YYYY-MM-DD` date when a human last checked the entry.
- `source_type`: one of `official`, `official/manufacturer`, `dealer`, `forum/used_market`, or `used_market`.

## Maintenance Rules

- Update `last_reviewed` whenever the URL, description, or caveat is checked.
- Do not claim inventory is available unless that was explicitly verified and recorded.
- Prefer manufacturer/dealer/category pages over random old forum threads.
- Keep compatibility caveats clear, especially for pedal steel tone bars versus lap steel or dobro slides.
- Do not add private contact information, emails, paid-only sources, or scraped forum posts as curated vendor entries.
