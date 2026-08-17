# Howdy Cloudflare Deployment Handoff

## Outcome

- Deployed the deterministic Howdy companion to `https://howdy.steelguitarrag.com/howdy`.
- The preview is public and ungated for this review, so Travis can open it without a Cloudflare Access login.
- Search indexing is disabled with `X-Robots-Tag: noindex, nofollow, noarchive`.
- No email or invitation was sent to Travis in this task.

## Deployment

- Cloudflare Pages project: `steel-guitar-rag-travis-preview`
- Deployment method: reviewed Direct Upload bundle
- Companion revision: `howdy-transcribed-review-2026-08-17.9`
- Git SHA: `c89b53d6bc77abcae72e1bd5747185df79aa0049`
- Deployment ID: `bd299474-cf8d-460f-85b8-468e0676509d`
- Private release manifest: `tmp/howdy-owner-review-2026-08-17.26.release-manifest.json`
- The private manifest records the immutable Pages deployment URL for rollback.

## Live verification

- `/` returns `302` to `/howdy`.
- `/howdy/`, `/howdy/embed-demo/`, `/howdy/print/`, and `/practice-guide/howdy/` return `200`.
- Canonical JSON, the backing-track MP3, and the printable PDF return `200` from the content-hashed asset directory.
- `/api/answer`, `/api/search`, `/ui/example`, `/chat`, `/melody`, and `/lessons` return `404`.
- An encoded directory traversal request returns `400`.
- The browser-loaded companion displays revision `.9`, build `c89b53d6bc77`, a 100% playback default, the 3:57 full-song view, and working Chords/NNS chart switching.
- Headers verified: same-origin CSP, `no-store` HTML caching, `no-referrer`, `nosniff`, `DENY` framing, and `noindex`.

## Isolation and rollback

- The hostname points only to the dedicated Pages project and does not route through `app.steelguitarrag.com`, the Mac mini, Ollama, Chroma, or general RAG APIs.
- Roll back by promoting the prior immutable Pages deployment in the dedicated project; do not alter the main app project or Mac mini runtime.

## Files changed

- Created this handoff.
- The hostname change was committed separately in `c89b53d6`.
- Existing unrelated worktree changes and untracked files were not staged or modified.
