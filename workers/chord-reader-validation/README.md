# Chord Reader — Travis Validation Worker

This dedicated Worker serves the private 15-song validation pilot, streams its
audio from a private R2 bucket, and saves per-song reviewer feedback to D1.
Every application and API route fails closed unless Cloudflare Access identifies
the exact email configured by the `TRAVIS_EMAIL` Worker secret.

## Local development

```bash
cp workers/chord-reader-validation/.dev.vars.example workers/chord-reader-validation/.dev.vars
npx wrangler d1 migrations apply DB --local --config workers/chord-reader-validation/wrangler.jsonc
npx wrangler dev --config workers/chord-reader-validation/wrangler.jsonc --port 8792
```

Local requests must include
`X-Travis-Validation-Reviewer: reviewer@example.invalid`. Production ignores
that header and requires `ctx.access` from Cloudflare Access.

## Production requirements

1. Provision the production D1 database and private R2 bucket named in
   `wrangler.jsonc`.
2. Apply D1 migrations remotely.
3. Upload `app/index.html`, `app/validation.css`, `app/validation.js`,
   `proof/proof.json`, and the fixed `audio/*.mp3` pilot objects to R2.
4. Set `TRAVIS_EMAIL` with `wrangler secret put`; never commit the address.
5. Deploy the production Worker to
   `https://travis-validation.steelguitarrag.com`.
6. Before allowing use, protect all Worker traffic with Cloudflare Access and
   an exact-email allow policy for the same address.

The browser JSON download remains available as a backup, but the normal review
workflow writes every changed track to D1 automatically.
