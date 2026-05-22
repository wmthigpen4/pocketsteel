# Corpus License Policy

This policy describes how The Turnaround should treat source permissions and corpus metadata. It is not legal advice.

## Policy Goals

- Preserve provenance for every source used in the corpus.
- Keep raw scraped data intact.
- Separate ingestion from copyright review.
- Avoid premature deletion, filtering, or destructive rewriting while SGF scraping is still active.
- Make future retrieval filtering explicit, testable, and reversible.

## Source Policy Snapshots

Source policy snapshots live under:

```text
corpus_metadata/source_policies/
```

A snapshot should capture the relevant public source terms, review notes, retrieval policy, and the date it was recorded. Snapshots should be append-only where possible so future changes in source terms do not erase historical context.

## Source Registry

`corpus_metadata/source_registry.json` is the source-level index. It should map source IDs to:

- source name
- source system
- source URL
- policy snapshot ID
- license policy ID
- current corpus use status
- notes

The registry is scaffolding for now. It should not block ingestion and should not be required by the scraper.

## Clean Corpus Metadata

Clean records can carry optional policy fields:

- `source_registry_id`
- `source_policy_id`
- `source_policy_snapshot_id`
- `source_policy_snapshot_date`
- `source_policy_url`
- `license_policy_id`
- `copyright_review_status`
- `copyright_flags`
- `copyright_notes`

These fields are not required yet. Null or empty values mean "not reviewed" rather than "approved" or "rejected."

## Retrieval Policy

During the current ingestion phase, retrieval should not filter on copyright flags because review metadata is not populated yet.

In a later phase, retrieval filtering may use reviewed metadata to exclude or down-rank sources that should not be used for answers. That change should be tested separately and documented before rollout.

## Future Review Queue

After scraping is complete, copyright scanning can create review queues for:

- possible copied articles or long reposts
- lyrics or tab-like copyrighted material
- private or paid lesson transcript indicators
- posts requiring manual source-policy review

The review queue should reference source records and derived corpus IDs. It should not rewrite raw scrape files.

