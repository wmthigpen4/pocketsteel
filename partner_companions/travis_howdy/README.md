# Travis Toy Tutorials - Howdy companion

This directory contains the reusable, deterministic source for the isolated
Howdy lesson companion. It deliberately does not import the Steel Guitar RAG
application shell, answer client, retrieval stack, accounts, corpus, or
navigation.

The tracked draft proves the product and packaging contract. It is not the
approved musical transcription. Unreviewed chord symbols are withheld instead
of guessed, every draft event is marked `musicalVerified: false`, and the UI
and PDF carry a review-required banner.

The ignored owner-review artifact may additionally carry a timestamped
technical lesson index and an audio-derived chord chart. Those labels remain
visibly review-required until Travis approves them; they are not promoted into
the tracked draft or a release artifact by browser code.

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

All presentations load one `lesson_companion_v1` JSON artifact. A reviewed
artifact may define two deterministic playback scopes tied to one source
recording: `fullSong` covers the complete backing track, while `taughtSolo`
identifies the exact lesson passage used by tab, fretboard, phrase stepping,
and looping. The private bundle packages the full recording and a hash-pinned
copy of that exact excerpt so both scopes seek reliably in static preview
runtimes.
Browser logic
is limited to deterministic indexed lesson search, authored layer switching,
an authored clock or same-origin audio, speed, phrase looping, step-by-step
move study, seeking, chord/solo state highlighting, fretboard and tab drawing,
print, and feedback-context assembly. There is no generative or retrieval
client.

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

A local owner-review bundle may also use a private, hash-pinned full backing track
without turning on release mode:

```bash
.venv/bin/python scripts/package_travis_companion.py \
  --output tmp/travis-preview-draft \
  --companion ~/.steel-rag/travis-preview/howdy/howdy.transcribed-review.json \
  --draft-audio ~/.steel-rag/travis-preview/howdy/howdy-full-song-preview.mp3 \
  --draft-solo-audio ~/.steel-rag/travis-preview/howdy/howdy-backing-solo-preview.mp3 \
  --draft-pdf output/pdf/Howdy-transcript-backed-review.pdf
```

The companion JSON must contain both files' exact SHA-256 values and exact
`fullSong` and `taughtSolo` ranges. The short hash-pinned file is the verified
audio excerpt at the recorded full-song offset and remains review evidence plus
a portable fallback. The browser loads the same-origin full recording before
seeking so local static runtimes do not need to implement MP3 byte ranges.
The packager copies
the audio and rendered review PDF only into the ignored local bundle; Git is
never an input or output for the private media. The current owner-review UI
keeps the lesson key visible, searches seven timestamped technical moments,
uses `0hA` for an open-position A-pedal hammer, exposes the complete song in
Full Song, and keeps the lesson's solo tab and phrase loops inside the exact
taught-solo audio window.

Full Song has its own horizontally scrolling chord/NNS lane, synchronized to
the complete recording. A complete reviewed chart can be supplied as the
optional root-level `songChordTimeline`; it must be contiguous and cover the
entire full-song duration. Until that authored chart is attached, the lane
places the current lesson-solo chord events at their absolute song times and
labels every other region `Chart pending`. The browser never analyzes audio or
guesses a missing chord.

Create the review-coded full-song chart outside the learner runtime with the
existing deterministic Play Along reader:

```bash
node scripts/author_travis_song_chords.js \
  --audio /private/howdy-full-song.mp3 \
  --companion /private/howdy-review.json \
  --output /private/howdy-review-next.json \
  --revision howdy-transcribed-review-YYYY-MM-DD.N
```

The authoring command pins the companion's known key, meter, and tempo, forces
one D-major song context, preserves the reader's confidence and attention
metadata, and replaces the taught-solo window with the companion's exact
source-timed solo chord events. The generated `songChordTimeline` remains
unapproved until Travis reviews it.

## Approved private inputs

The release bundle must be assembled from a private directory outside Git,
for example `/Users/cory/.steel-rag/travis-preview/howdy/`. That location
contains:

- an approved companion JSON with exact chord, bar, beat, phrase, solo,
  notation, tab, technique, and copedent data;
- the licensed backing-track file;
- the reviewed taught-solo excerpt derived from that backing track;
- an approved black-and-white pedal-steel brand image;
- the approved Metropolis webfont used by the school;
- `release-config.json`, based on `release-config.example.json`, with exact
  file hashes, approval references, feedback address, the current review
  phase, tester identities, and three Cloudflare Access application IDs.

The initial `owner_only` phase requires exactly one private tester identity.
That identity is supplied through the ignored private release configuration;
it is never written into the deployment bundle or release manifest. The
`partner_review` phase requires exactly two identities and must be selected
explicitly in a later release configuration after partner access is approved.

Release packaging requires all of these conditions:

- `contentStatus: "approved"`;
- `reviewPhase: "owner_only"` with exactly one Access tester email for the
  initial review, or an explicitly promoted `partner_review` phase with
  exactly two;
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
  --companion ~/.steel-rag/travis-preview/howdy/howdy.approved.json \
  --release-config ~/.steel-rag/travis-preview/howdy/release-config.json \
  --output tmp/travis-preview-release \
  --manifest ~/.steel-rag/travis-preview/howdy/release-manifest.json
```

Running the publisher without its final acknowledgement performs another
verification and does not upload:

```bash
.venv/bin/python scripts/publish_travis_companion.py \
  --bundle tmp/travis-preview-release \
  --manifest ~/.steel-rag/travis-preview/howdy/release-manifest.json
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
