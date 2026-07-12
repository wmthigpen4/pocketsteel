# Melody Studio public-domain songbook expansion plan

## Task summary

Reviewed the request for numerous public-domain melody examples against the current implementation. Melody Studio already has a reviewed, checksummed `score_draft_v1` catalog format and one entry, Amazing Grace / NEW BRITAIN. However, the catalog API, catalog import adapter, and `Try an example song` control are currently coupled to `features.melodyImport`; the protected preview keeps that feature disabled, so the reviewed catalog is not generally discoverable.

Recommended a first **12-song reviewed songbook** development slice that decouples built-in examples from user uploads/imports and makes the songbook a clear contextual action inside Add a melody.

## Proposed starter repertoire

Treat these as candidates until the exact tune/version and primary-source record are reviewed:

1. Amazing Grace / NEW BRITAIN (existing)
2. Oh! Susanna
3. Aura Lee
4. Buffalo Gals
5. Skip to My Lou
6. She'll Be Coming 'Round the Mountain
7. When the Saints Go Marching In
8. Red River Valley
9. Shenandoah
10. My Bonnie Lies over the Ocean
11. Wayfaring Stranger
12. Careless Love

The final pack may substitute a candidate if its specific melody/version cannot be sourced cleanly. Candidate status must never be presented as verified status.

## Product behavior

- Rename `Try an example song` to `Browse songbook` and show a song count.
- Keep it as a contextual action inside Type or tap notes rather than adding another equal top-level entry method.
- Open a compact songbook browser with title search and filters for difficulty, meter, and feel.
- Cards show title, tune/version, key, meter, difficulty, event/section count, and source attribution.
- Opening a song transitions directly to the existing Review melody staff.
- Arrange for E9 uses the existing single-note, harmony, thirds, sixths, chord-melody, score, fretboard, tab, and print-tab behavior.
- Longer songs are divided into numbered sections; do not truncate silently or render an oversized single response.
- The initial pack should provide one complete verse/chorus melody where it fits the reviewed score limits. Longer material uses reviewed sections under one song record.

## Catalog and feature contract

- Add `features.melodyCatalog=true` whenever the reviewed built-in songbook is enabled.
- Do not require `features.melodyImport` for `GET /api/melody/catalog` or opening a reviewed catalog draft.
- Keep user file/image/MusicXML/MIDI import under `melodyImport`.
- Keep authentication requirements unchanged.
- No persistence, scraping, corpus ingestion, embeddings, Chroma, or automatic link transcription.

## Per-song requirements

- exact title and tune/version identity;
- primary source URL and concise attribution;
- reviewed public-domain status for the specific source melody/version;
- source checksum;
- G or C arrangement key for current deterministic support;
- meter, pickup, rhythmic durations, pitch values, and optional chord changes;
- section metadata for longer melodies;
- `review.status=confirmed` and no unresolved warnings;
- mechanical E9 validation for every rendered route;
- top melody voice preserved in harmonized/chord-melody score output;
- current-route tablature print coverage.

## Verification plan

- Test catalog card metadata, stable ordering, unique ids, checksums, rights labels, source URLs, and confirmed review state.
- Test every score draft through normalization, reflow, score rendering, melody arrangement, and tab validation.
- Test every pitch remains within the selected G/C major context unless explicitly marked chromatic and supported.
- Test section continuation and complete event coverage.
- Test songbook availability with `melodyCatalog=true` and `melodyImport=false`.
- Test upload/import remains unavailable when `melodyImport=false`.
- Test search/filter, keyboard access, mobile containment, source attribution, Edit melody, Start over, and Print tablature.
- Run focused catalog/API/arranger/UI tests, full pytest, local browser smoke, exact-path commit, protected-preview refresh, `/api/version`, authenticated protected smoke, and integration refresh before user smoke.

## Files changed

- `docs/handoffs/task-completions/2026-07-11-2340-18-public-domain-songbook-expansion-plan.md`

No runtime, catalog data, tests, feature flags, auth, deployment, corpus, source-inbox, private-data, or assets changed.

## Tests and checks

- Inspected the existing Amazing Grace catalog record, loader, API gating, UI adapter, and related tests.
- Confirmed the current protected-status handoff reports import/catalog visibility as disabled.
- Reviewed a Library of Congress 1849 Oh! Susanna score record as an example primary-source trail; final implementation requires per-song review.
- `git diff --check -- docs/handoffs/task-completions/2026-07-11-2340-18-public-domain-songbook-expansion-plan.md` — required before closeout.
- No runtime tests were run because this task is a product/architecture proposal only.

## Integration notes

- The current `_CATALOG_FILES` mapping contains only `amazing-grace-new-britain`.
- `GET /api/melody/catalog`, catalog draft loading, and the frontend song entry are currently coupled to `melodyImport`.
- This is a data-heavy feature: each melody and harmony body requires review, not automated generation from memory.

## Risk assessment

Medium. The implementation path is established, but inaccurate tune variants, rhythm, harmony, or rights/source metadata would undermine the teaching product. Exact version identity and mechanical validation are required for every song.

## Human decision needed

Yes. Approve the 12-song starter pack, the candidate repertoire with substitution allowed after source review, and decoupling the built-in songbook from file imports.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-11-2340-18-public-domain-songbook-expansion-plan.md`

## Files that must not be staged

Every other modified or untracked path, including the separate unapproved octave-help recommendation, corpus, source-inbox, private-data, deployment, public/brand, `ui/brand/`, `Neon Sign/`, generated reports, and unrelated docs/runtime files.

## Recommended next lane

After approval: `18 Product / Architecture` for the final per-song source manifest, then `05 Backend / RAG Integration` and `06 UX/UI Design` in the approved Autopilot loop, with `15 QA`, `01 Repo Steward`, and `12 Self-Hosted Deployment` completing delivery.

## Commit readiness

Needs human review first

## Suggested next step

Approve the 12-song reviewed songbook slice and allow candidate substitution when a specific tune/version lacks a clean primary-source record.
