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
- Companion revision: `howdy-transcribed-review-2026-08-17.12`
- Git SHA: `0dde0a4e7e31dfe0a673051d1ac2075c8a5ecf56`
- Deployment ID: `1b5cb02c-4d29-4632-8454-637730a63fba`
- Access application: `Howdy Travis Review` (`ef2da6de-d8d2-49a0-931f-2e9e751fed38`)
- Access policy: `Howdy — Cory and Travis only` (`768322a3-7273-46f1-a9d4-cdf293c13df1`)
- Protected destinations: `howdy.steelguitarrag.com`, the production Pages hostname, and wildcard Pages deployment aliases.
- Private release manifest: `tmp/howdy-owner-review-2026-08-17.31.release-manifest.json`
- The private manifest records the immutable Pages deployment URL for rollback.

## Bundle verification before the Access gate

- `/` returns `302` to `/howdy`.
- `/howdy/`, `/howdy/embed-demo/`, `/howdy/print/`, and `/practice-guide/howdy/` return `200`.
- Canonical JSON, the backing-track MP3, and the printable PDF return `200` from the content-hashed asset directory.
- `/api/answer`, `/api/search`, `/ui/example`, `/chat`, `/melody`, and `/lessons` return `404`.
- An encoded directory traversal request returns `400`.
- The browser-loaded companion displays revision `.12`, build `0dde0a4e7e31`, a 100% playback default, the 3:57 full-song view, and working Chords/NNS chart switching.
- The full-song chord lane remains stationary during playback. Its current-chord indicator still follows the audio.
- The taught-solo guide below the player advances manually through 54 authored moves. Advancing the guide does not pause or seek full-song playback, and the compact tablature remains visible.
- The compact tablature is one horizontally scrollable 54-move lane. Selecting a beat column updates Travis's guidance below the tablature; taught-solo playback follows and scrolls the active column.
- Owner correction applied to bar 1: beat 1.1.5 remains the open-to-fret-1 hammer; beats 1.2 through 1.3.5 now remain at fret 2, ending with `2B`. Tab, pitch labels, fretboard state, guidance, and the generated PDF share those corrected events.
- Headers verified: same-origin CSP, `no-store` HTML caching, `no-referrer`, `nosniff`, `DENY` framing, and `noindex`.

## Access verification

- Anonymous requests to `/`, `/howdy/embed-demo/`, and the backing-track MP3 now return `302` to the Cloudflare Access login flow instead of companion content.
- Anonymous requests to `steel-guitar-rag-travis-preview.pages.dev` also return the Access login redirect.
- Anonymous requests to the immutable deployment alias `1b5cb02c.steel-guitar-rag-travis-preview.pages.dev` return the Access login redirect through the wildcard destination.
- The allow policy contains exactly two named email values and remains default-deny for every other identity.

## Isolation and rollback

- The hostname points only to the dedicated Pages project and does not route through `app.steelguitarrag.com`, the Mac mini, Ollama, Chroma, or general RAG APIs.
- Roll back by promoting the prior immutable Pages deployment in the dedicated project; do not alter the main app project or Mac mini runtime.

## Files changed

- Created this handoff.
- The interactive scrolling tablature behavior was committed separately in `f3e4caa0`.
- Existing unrelated worktree changes and untracked files were not staged or modified.
