# Play Songs catalog pipeline plan

## Task summary

Reframed Play Songs from a small public-domain song list into a repeatable
catalog-acquisition and lesson-authoring pipeline. The durable plan prioritizes
device-only modern tracks, direct artist-authorized collections, and an eventual
B2B licensed catalog. Owned and open-license recordings remain quality fixtures,
not the long-term catalog strategy.

## Files changed

- `docs/play-songs-catalog-pipeline.md`
- `docs/handoffs/task-completions/2026-08-02-1505-18-play-songs-catalog-pipeline-plan.md`

No runtime, catalog, audio, rights record, authentication, deployment, corpus,
private source, or saved user data changed.

## Tests and checks

- Inspected the current song-practice contract, curated registry, authoring
  plan, and readiness-gate handoff.
- Reviewed current official/public materials for synchronization licensing,
  the MLC audio-only boundary, Apple MusicKit, Stingray Karaoke API, Hal Leonard
  licensing, and licensed application-music providers.
- `git diff --check` required before closeout.

## Risks

Medium product and rights risk. Commercial catalog access does not by itself
authorize synchronized lyrics, tablature, instructional derivatives, looping,
speed changes, or offline caching. Every provider must approve the exact use in
writing. Device-only analysis reduces distribution risk but still requires a
strict no-audio/no-identifying-metadata network boundary.

## Human decision needed

Approve Phase 1 as the next implementation slice: private candidate and rights
schemas, validation/reporting, public catalog cleanup, and one new golden
pipeline fixture. Vendor outreach and direct-artist contracting require later
business authorization; no vendor has been selected or contacted.

## Safe-to-stage exact file list

- `docs/play-songs-catalog-pipeline.md`
- `docs/handoffs/task-completions/2026-08-02-1505-18-play-songs-catalog-pipeline-plan.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-07-23-1603-20-canonical-validation-review-ready.md`
- unrelated historical handoffs and generated files
- audio, rights metadata dumps, releases, logs, credentials, secrets, corpus
  data, vector stores, or private training data

## Recommended next lane

Lane 18 approval, then Lane 05 for the candidate/readiness contract, Lane 06
for the internal curation view and device-only flow, Lane 15 for musical and
privacy gates, and Lane 01 for exact-path commit hygiene.

## Commit readiness

The docs-only plan is ready for exact-path staging after `git diff --check`.
