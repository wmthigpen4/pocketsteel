# Howdy Cloudflare Deployment Handoff

## Outcome

- Deployed the deterministic Howdy companion to `https://howdy.steelguitarrag.com/howdy`.
- The preview is protected by a dedicated Cloudflare Access application. Only the two named reviewer email addresses are allowed.
- Authentication uses emailed one-time PINs and instant authentication; no other identity provider is enabled for this application.
- Search indexing is disabled with `X-Robots-Tag: noindex, nofollow, noarchive`.
- No email, invitation, or login code was sent to Travis while configuring access.

## Deployment

- Cloudflare Pages project: `steel-guitar-rag-travis-preview`
- Deployment method: reviewed Direct Upload bundle
- Companion revision: `howdy-transcribed-review-2026-08-17.20`
- Git SHA: `34dd518642cc97f64e2aba2951d3b82bd7474277`
- Deployment ID: `e10dc1e6-d8a7-4907-9bd1-73e2b8dc67f8`
- Immutable deployment URL: `https://e10dc1e6.steel-guitar-rag-travis-preview.pages.dev`
- Access application: `Howdy Travis Review` (`ef2da6de-d8d2-49a0-931f-2e9e751fed38`)
- Access policy: `Howdy — Cory and Travis only` (`768322a3-7273-46f1-a9d4-cdf293c13df1`)
- Protected destinations: `howdy.steelguitarrag.com`, the production Pages hostname, and wildcard Pages deployment aliases.
- Private release manifest: `tmp/howdy-owner-review-2026-08-17.39.release-manifest.json`
- The private manifest records the immutable Pages deployment URL for rollback.

## Bundle verification before the Access gate

- `/` returns `302` to `/howdy`.
- `/howdy/`, `/howdy/embed-demo/`, `/howdy/print/`, and `/practice-guide/howdy/` return `200`.
- Canonical JSON, the backing-track MP3, and the printable PDF return `200` from the content-hashed asset directory.
- `/api/answer`, `/api/search`, `/ui/example`, `/chat`, `/melody`, and `/lessons` return `404`.
- An encoded directory traversal request returns `400`.
- The browser-loaded companion displays revision `.20`, build `34dd518642cc`, a 100% playback default, the 3:57 full-song view, and working Chords/NNS chart switching.
- The full-song chord lane remains stationary during playback. Its current-chord indicator still follows the audio.
- The taught-solo guide below the player advances manually through 54 authored moves. Advancing the guide does not pause or seek full-song playback, and the compact tablature remains visible.
- The compact tablature is one horizontally scrollable 54-move lane. Selecting a beat column updates Travis's guidance below the tablature; taught-solo playback follows and scrolls the active column.
- The redundant standalone `Selected phrase` card was removed. Phrase title, note, bar range, and move count now sit directly above the tablature in the Taught Solo card; feedback remains in the main practice flow below the fretboard. The practice area is a single column, and browser DOM verification found zero `Selected phrase` labels and exactly one integrated phrase summary.
- Owner correction applied to bar 1: the open-to-fret-1 hammer lands at beat 1.1.5 and the bar remains at fret 1 through beat 1.3.5, ending with `1B`. Tab, pitch labels, fretboard state, guidance, and the generated PDF share those corrected events.
- The printable taught solo is one ink-light 11-by-8.5-inch landscape letter page (`792 x 612` points) with no notation staff or solid-color masthead. It includes the official TTT logo, `travistoytutorials.com`, an Eddy Dunlap performance credit, compact chord/key context, four wide two-bar tab systems, and an AI-generated/human-reviewed limitation note covering omitted slides, squeezes, and copedent-specific actions. `Page 1 of 1` and the Steel Guitar RAG attribution remain removed. All ten tablature string lines in every system extend to the right print margin. The rasterized page was inspected; bars 1-8, movement labels, and the footer remain inside the print-safe area without overlap or clipping. The browser print stylesheet also declares `letter landscape`.
- `/howdy/print` and `/howdy/print/` now redirect to the same content-hashed canonical PDF used by the companion's PDF action. The separate HTML tablature rendition is no longer packaged or reachable, eliminating print-layout drift.
- Taught-solo and full-song playback no longer advance or reposition the tablature. Only a tab-column click or the Previous/Next controls can change the selected move.
- Headers verified: same-origin CSP, `no-store` HTML caching, `no-referrer`, `nosniff`, `DENY` framing, and `noindex`.

## Access verification

- Anonymous requests to `/`, `/howdy/embed-demo/`, and the backing-track MP3 now return `302` to the Cloudflare Access login flow instead of companion content.
- Anonymous requests to `steel-guitar-rag-travis-preview.pages.dev` also return the Access login redirect.
- Anonymous requests to the immutable deployment alias `e10dc1e6.steel-guitar-rag-travis-preview.pages.dev` return the Access login redirect through the wildcard destination.
- The allow policy contains exactly two named email values and remains default-deny for every other identity.

## Isolation and rollback

- The hostname points only to the dedicated Pages project and does not route through `app.steelguitarrag.com`, the Mac mini, Ollama, Chroma, or general RAG APIs.
- Roll back by promoting the prior immutable Pages deployment in the dedicated project; do not alter the main app project or Mac mini runtime.

## Files changed

- Created this handoff.
- The wide landscape print composition was committed in `34dd518642cc`.
- Existing unrelated worktree changes and untracked files were not staged or modified.
