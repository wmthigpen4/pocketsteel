# Travis Toy Tutorials - Howdy companion

This directory contains the reusable, deterministic source for the isolated
Howdy lesson companion. It deliberately does not import the Steel Guitar RAG
application shell, answer client, retrieval stack, accounts, corpus, or
navigation.

The tracked draft proves the product and packaging contract. It is not the
approved musical transcription. Unreviewed chord symbols are withheld instead
of guessed, every draft event is marked `musicalVerified: false`, and the UI
and PDF carry a review-required banner.

## Presentations

- `/howdy` is the expanded Travis Toy Tutorials practice workspace.
- `/howdy/embed-demo` puts the compact companion under a simulated lesson
  video area using the inspected Metropolis, `#134361`, `#ff3f20`, white,
  soft-gray, and 6 px-radius treatment. It does not reproduce Teachable's
  player or logo.
- `/howdy/print` is the browser-print surface. The packaged PDF is generated
  from the same phrase and event IDs.
- `/` redirects to `/howdy`.
- Every other path falls through to the root `404.html`, which Cloudflare
  Pages serves with status 404.

All presentations load one `lesson_companion_v1` JSON artifact. Browser logic
is limited to an authored clock or same-origin audio, speed, phrase looping,
seeking, event highlighting, fretboard and tab drawing, display mode, print,
and feedback-context assembly. There is no generative or retrieval client.

## Local draft

Install the print dependencies once:

```bash
.venv/bin/pip install -e '.[companion]'
```

Build and verify the allowlisted draft:

```bash
npm run build:travis-preview:draft
npm run verify:travis-preview
```

Run it through Cloudflare's local Pages runtime:

```bash
npx wrangler pages dev tmp/travis-preview-draft \
  --ip 127.0.0.1 \
  --port 8899 \
  --compatibility-date 2026-08-14 \
  --persist-to tmp/wrangler-travis-preview \
  --show-interactive-dev-session false
```

The standalone printable draft can be regenerated with:

```bash
.venv/bin/python scripts/generate_travis_tablature_pdf.py \
  --companion partner_companions/travis_howdy/content/howdy.draft.json \
  --output output/pdf/Howdy-companion-draft.pdf
```

## Approved private inputs

The release bundle must be assembled from a private directory outside Git,
for example `/Users/cory/.steel-rag/travis-preview/howdy/`. That location
contains:

- an approved companion JSON with exact chord, bar, beat, phrase, solo,
  notation, tab, technique, and copedent data;
- the licensed backing-track file;
- an approved black-and-white pedal-steel brand image;
- the approved Metropolis webfont used by the school;
- `release-config.json`, based on `release-config.example.json`, with exact
  file hashes, approval references, feedback address, tester identities, and
  three Cloudflare Access application IDs.

Tester emails are used to validate the two-person release gate but are not
written into the deployment bundle or release manifest.

Release packaging requires all of these conditions:

- `contentStatus: "approved"`;
- exactly two Access tester emails;
- every approval flag true;
- every solo event `musicalVerified: true`;
- every chord boundary `verified: true` with a reviewed symbol;
- approved source copedent and print layout;
- at least five human approval references;
- exact SHA-256 matches for audio and approved brand imagery;
- three Access applications recorded: custom domain, production
  `pages.dev`, and preview `*.pages.dev`;
- anonymous-denial results for all three Access surfaces;
- the existing `app.steelguitarrag.com` policy recorded as unchanged;
- committed, byte-identical static source files.

Package the private release into a temporary Direct Upload directory:

```bash
SOURCE_DATE_EPOCH=<approved-unix-time> \
.venv/bin/python scripts/package_travis_companion.py \
  --release \
  --companion /Users/cory/.steel-rag/travis-preview/howdy/howdy.approved.json \
  --release-config /Users/cory/.steel-rag/travis-preview/howdy/release-config.json \
  --output tmp/travis-preview-release \
  --manifest /Users/cory/.steel-rag/travis-preview/howdy/release-manifest.json
```

Running the publisher without its final acknowledgement performs another
verification and does not upload:

```bash
.venv/bin/python scripts/publish_travis_companion.py \
  --bundle tmp/travis-preview-release \
  --manifest /Users/cory/.steel-rag/travis-preview/howdy/release-manifest.json
```

Only after Access and custom-domain verification should the same command be
run with `--deploy-reviewed-bundle`. The publisher always targets the
dedicated `steel-guitar-rag-travis-preview` Pages project, records the
immutable deployment URL in the private manifest, and reports the branded URL
for sharing.

## Content revision rules

Any change to musical content, chord boundaries, copedent, attribution,
phrase structure, backing audio, brand imagery, or print layout requires a
new companion revision and fresh approvals. Browser code cannot promote an
alternate position into the approved route. The artifact hash covers the
canonical companion data, while the approved-content hash also covers the CSS
and JavaScript and becomes the versioned asset directory.

## Future Teachable route

The preview route is intentionally protected with `frame-ancestors 'none'`.
After Travis approves the content and UX, create a separate final embed route
that permits framing only from his exact Teachable school origins, complete
the `courses:read` enrollment check, and add that URL to a private test
lesson. Cloudflare Access remains preview-only so an Access login is never
placed inside the final iframe.
