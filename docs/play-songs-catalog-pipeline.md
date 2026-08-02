# Play Songs catalog and authoring pipeline

## Outcome

Build a repeatable system that can discover, clear, author, verify, and publish
high-quality Play Along lessons. Public-domain songs remain useful golden
fixtures, but the catalog strategy is modern music that steel players actually
want to learn.

No song appears in **Starter Songs** until its recording rights, musical data,
steel lesson, and playback synchronization pass one atomic publication gate.
An identified title or permissively licensed recording is not a lesson.

## Catalog strategy

Use four acquisition lanes, in this order:

1. **Bring Your Own Track — device only.** This is the fastest path to modern
   songs. The user selects audio already on the device; audio analysis and
   project storage remain on-device, and no audio bytes are sent to Steel Guitar
   RAG. The confirmed local timeline drives the same player as bundled songs.
2. **Artist-authorized modern songs.** Recruit independent country, Americana,
   gospel, and steel-adjacent artists who can directly clear both the composition
   and master, or identify every required rights holder. Begin with a small
   featured-artist collection rather than chasing individual major-label hits.
3. **Licensed commercial catalog.** After Play Along demonstrates repeat use,
   negotiate a B2B pilot with a music-education, karaoke, or application-music
   provider. The agreement must explicitly cover on-demand playback, synchronized
   instructional visuals, lyrics where used, looping, speed changes, caching,
   derived chord/tab guidance, territories, term, reporting, and takedowns.
4. **Owned, public-domain, and open-license fixtures.** Use commissioned masters
   and carefully selected CC recordings to test the pipeline and teach durable
   fundamentals. Do not pad the visible catalog with weak recordings merely
   because they are easy to license.

Consumer streaming SDKs may be evaluated as playback sources, but catalog access
must never be treated as permission to publish synchronized lyrics, tablature,
or an adapted instructional experience. The MLC blanket license is audio-only
and does not cover audiovisual synchronization. A synchronized Play Along use
therefore requires a purpose-specific rights analysis and agreement.

## What qualifies as a suitable song

Score every candidate before rights outreach:

| Dimension | Weight | Requirement |
|---|---:|---|
| Learner demand | 30% | Recognizable or strongly requested by the target steel audience |
| Steel teaching value | 20% | Teaches transferable grips, movement, phrasing, pedals, or levers |
| Recording suitability | 20% | Clear time, audible harmony/melody, useful arrangement, and room for the player |
| Rights feasibility | 20% | Identifiable composition and master owners with a realistic clearance path |
| Authoring cost | 10% | Form, meter, tuning, tempo drift, and complexity fit the planned lesson tier |

Reject a candidate when the master sounds synthetic or amateurish, the harmony
is hard to hear, the recording already contains a competing steel part, the
form is unsuitable for a beginner lesson, the rights chain is incomplete, or
the title cannot justify its authoring cost.

Maintain a balanced target queue rather than a random song list:

- 40% beginner chord-foundation songs;
- 30% signature steel vocabulary and fills;
- 20% melody-led or chord-melody lessons;
- 10% advanced showcases.

## Required catalog records

Add an internal, versioned `SongCandidate` registry separate from the public
curated lesson registry. A candidate is never returned by the public Songs API.

Each candidate records:

- stable candidate id, title, artist, release, genre, demand evidence, and
  teaching hypothesis;
- acquisition lane and current state;
- composition owners, publishers, master owners, performers, and contact path;
- proposed recording, duration, territory, and source provenance;
- audio-quality notes and rejection reasons;
- rights request, allowed uses, term, territories, attribution, reporting,
  takedown procedure, and immutable approval reference;
- authoring owner, reviewer, timestamps, fixture versions, and publication id.

The state machine is:

```text
identified
  -> screened
  -> rights_inquiry
  -> rights_cleared
  -> master_approved
  -> timeline_authored
  -> e9_lesson_authored
  -> qa_passed
  -> published
```

Any gate may transition to `rejected` or `on_hold` with a reason. Only
`published` candidates are copied into `CuratedPracticeLesson` and receive
`playAlongReady: true`.

## Rights gate for modern songs

The clearance packet must separately identify the musical composition and the
sound recording. It must explicitly answer whether Steel Guitar RAG may:

- stream or bundle the chosen master on demand;
- synchronize it with chord, fretboard, lyric, and tablature visuals;
- display all lyrics, partial lyrics, or no lyrics;
- publish a steel-guitar arrangement and mechanically derived positions;
- loop, seek, slow down, preserve pitch, and provide count-ins;
- cache encrypted or ordinary audio for offline reopening;
- use artwork, artist name, recording credit, and promotional excerpts;
- operate in each territory and subscription tier;
- retain usage analytics and deliver royalty reports;
- continue serving already-downloaded content after termination;
- respond to corrections, expirations, and takedown notices.

Do not infer these permissions from a mechanical license, consumer streaming
subscription, purchased download, public performance license, or a publisher's
print arrangement.

### Partner discovery

Run commercial discovery in parallel, without integrating a vendor until the
allowed use is in writing:

- **Stingray Karaoke API:** promising because its API is designed for an
  interactive karaoke catalog and supports position-preserving vocal/no-vocal
  playback. Confirm catalog fit, chord/beat metadata, lyric-display scope,
  derivative instructional overlays, pricing, and territories.
- **Hal Leonard / Muse Group:** promising for licensed education repertoire,
  arrangements, and digital materials. Request a platform agreement rather
  than assuming a purchased score grants application rights.
- **Feed.fm or a comparable licensed-music API:** investigate whether its
  commercial catalog can support user-selected full songs and synchronized
  instruction; its public products emphasize radio and clips, so the exact use
  must be negotiated.
- **Direct artist/publisher agreements:** preferred for the first modern
  collection because they can include stems, charts, lyrics, credits, and
  promotional participation in one package.

Apple Music, Spotify, YouTube, or another consumer service may be a future
playback integration only after both the platform terms and music rights permit
this exact synchronized teaching experience.

## Authoring pipeline

### 1. Ingest and fingerprint

- Store the approved source master outside the public catalog until cleared.
- Record cryptographic checksum, codec, duration, loudness, channel layout,
  sample rate, provenance, and rights-record digest.
- Create a working derivative only when the rights packet allows it.

### 2. Produce a machine draft

Run offline tooling or an isolated worker to estimate:

- tempo curve, meter, beat timestamps, downbeats, count-in, and sections;
- key centers, chord boundaries, chord symbols, rests, and no-chord spans;
- melody onsets and pitches when a melody-led lesson is planned;
- lyric alignment only when authorized lyrics are supplied;
- drift, rubato, repeats, pickup measures, and confidence values.

Machine output is a draft. It never becomes the authoritative timeline without
musical review.

### 3. Author the master timeline

An editor confirms the exact audio clock:

- beat and bar timestamps;
- section boundaries and form;
- chord changes, inversions where educationally relevant, and no-chord spans;
- lyric phrase timestamps where permitted;
- melody events for melody-led lessons;
- count-in, ending behavior, and loop-safe bar boundaries.

The editor must support waveform zoom, playback-rate changes, tap/replace
downbeat, nudge, section retap, drift correction, chord audition, undo, and
confidence review. The confirmed timeline becomes authoritative.

### 4. Author the steel lesson

Generate several mechanically valid E9 routes, then have a steel-aware reviewer
choose and explain them:

- **Chord Foundation:** continuity-first accompaniment;
- **Move the Bar:** common pockets and intentional position movement;
- **Stay in Position:** pedal/lever changes with minimal travel;
- **Follow the Melody:** exact reviewed melody on top using single notes, dyads,
  or grips as musically appropriate;
- **Full Chord Melody:** advanced only, with exact melody and validated harmony.

Routes change for a teaching reason—not for visual variety. Every event records
the exact string, fret, per-string control, pitch result, chord role, transition,
selection reason, and valid alternatives.

### 5. Musical and playback QA

Review the complete song by ear and against fixtures:

- every chord promotion follows the master within 50 ms for bundled lessons;
- lyric phrases and melody events agree with what is audible;
- every displayed grip is mechanically playable on the declared copedent;
- melody routes preserve pitch and register with the melody as the highest
  voice when promised;
- current and next instructions remain legible in phone landscape;
- seeking, looping, slow playback, pause/resume, count-in, and endings remain
  synchronized;
- attribution, license link, term, territory, and takedown metadata render as
  required;
- only the opened master downloads, and expired content cannot reopen.

QA requires two approvals: a musical reviewer and a rights/publication reviewer.

## Bring Your Own Track as the modern-song bridge

Finish the device-only workflow before negotiating a large catalog. It proves
that users want to practice modern songs without Steel Guitar RAG distributing
those masters.

The local flow should be:

1. Select a track from the device.
2. Produce tempo, beat, key, and chord drafts locally.
3. Optionally paste an authorized/personal chord chart and align it to the grid.
4. Confirm low-confidence chord and timing regions.
5. Generate E9 lesson routes.
6. Save audio in OPFS and metadata in IndexedDB.
7. Export metadata only; relink the recording when moving devices.

No server request may contain audio, filename, song title, artist, lyrics, or
other identifying media metadata. The server may arrange only anonymous,
confirmed timing/chord targets and copedent context, consistent with the
existing song-practice API boundary.

## Product presentation

- **Starter Songs** contains playable lessons only.
- Do not show rights inquiries, placeholders, or partially authored songs as
  disabled catalog cards.
- A separate **Coming Soon** row is allowed only for a cleared and actively
  authored song with a credible release window.
- Unfinished candidates remain in an authenticated internal curation view.
- Each published song card identifies the lesson types actually available;
  it does not promise melody instruction when only chord accompaniment exists.

## Operational metrics

Track:

- candidates screened, rejected, awaiting rights, cleared, authored, and
  published;
- median days from identification to rights decision;
- human authoring and review hours per published minute;
- timeline corrections per minute after the machine draft;
- playback/synchronization defects per lesson;
- starts, 30-second survival, completed sections, loop use, repeat plays, and
  return rate by song and lesson type;
- rights cost and royalty burden per active learner;
- takedown and expiration compliance.

Use these metrics to decide whether to fund a commercial catalog—not raw card
count.

## Implementation sequence

### Phase 1 — Make the pipeline real

1. Add private `SongCandidate` and `RightsRecord` schemas plus a validation CLI.
2. Add a curation report showing the exact missing gate for every candidate.
3. Move incomplete public cards out of Starter Songs.
4. Convert Amazing Grace into the golden end-to-end publication fixture.
5. Process one new owned/open recording through the pipeline without relaxing
   the quality gate.

### Phase 2 — Modern songs without catalog distribution

1. Complete on-device analysis, correction, relinking, and route generation.
2. Validate the flow on user-supplied modern recordings without retaining or
   transmitting identifying media data.
3. Measure which songs and lesson modes users actually practice using local-only
   product analytics that do not reveal track identity.

### Phase 3 — First authorized modern collection

1. Prepare a concise artist/publisher rights packet and submission portal.
2. Sign 5–10 direct-authorized modern country/Americana songs.
3. Prefer stems or accompaniment masters without steel where available.
4. Author and publish two songs first; expand only after musical user smoke.

### Phase 4 — Commercial catalog pilot

1. Send the exact product/rights requirements to Stingray, Hal Leonard/Muse,
   Feed.fm, and other qualified providers.
2. Compare usable repertoire, permitted interaction, metadata, economics,
   territories, reporting, and technical delivery.
3. Pilot roughly 25 recognizable songs under one written agreement.
4. Expand only if usage and retention justify licensing and authoring cost.

## Immediate next slice

Implement Phase 1 only. Do not spend more effort polishing random public-domain
recordings before the candidate registry, rights record, authoring checklist,
and hidden-until-ready publication gate exist. In parallel, prepare the partner
requirements brief and complete the device-only analysis design.

## Phase 1 implementation status

- Versioned `SongCandidate` and `RightsRecord` schemas: implemented.
- Non-public candidate and rights registries: implemented.
- Validation CLI and exact missing-gate report: implemented.
- Public Starter Songs restricted to fully published candidates: implemented.
- Amazing Grace golden publication fixture: implemented.
- New open recording pipeline exercise: the exact Grant Raymond Barrett **Hard
  Times Come Again No More** master is rights-verified, fingerprinted, and
  technically inspected. It is correctly stopped at `master` pending musical
  audition; no timeline or lesson will be fabricated to make the pipeline look
  complete.
