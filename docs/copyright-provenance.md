# Copyright and Provenance Plan

This is a planning document for The Turnaround. It defines the provenance and copyright review scaffolding only.

## Current Phase

SGF ingestion is still in progress. The current priority is preserving raw data and finishing ingestion.

Do not run copyright scanning in the active scrape pipeline yet.

Current rules:

- Preserve raw scraped data.
- Do not slow down or alter scraping.
- Do not delete or rewrite raw data.
- Do not scan the full corpus.
- Do not filter retrieval based on copyright flags yet.
- Do not require copyright metadata fields in clean corpus records yet.

## Scaffolding Added Now

The repository includes these inert structures:

- `corpus_metadata/source_registry.json`
- `corpus_metadata/source_policies/`
- Optional clean-corpus metadata fields for source policy and copyright review state

These structures are placeholders for later enrichment. They are not connected to the scraper, retrieval filters, or scan jobs.

## Optional Clean Corpus Fields

Clean corpus records may include:

- `source_registry_id`
- `source_policy_id`
- `source_policy_snapshot_id`
- `source_policy_snapshot_date`
- `source_policy_url`
- `license_policy_id`
- `copyright_review_status`
- `copyright_flags`
- `copyright_notes`

For now these fields are placeholders. Missing or null values must be treated as normal.

## Future Phase

After SGF scraping is complete, a separate enrichment phase can run:

- `scripts/scan_copyright_flags.py`
- metadata enrichment
- downstream retrieval filtering
- manual review queues

That future phase should operate on derived corpus artifacts. It should not mutate raw scrape outputs.

## Design Notes

Copyright flags should be treated as review signals, not proof of infringement. Automated scanning can identify likely issues, but source policy snapshots and manual review should control enforcement decisions.

Retrieval filtering should be added only after review metadata is populated and tested against representative queries.

