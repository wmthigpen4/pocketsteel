# Song Practice v1

## Product boundary

Song Practice is the deterministic song-learning path inside Melody Studio. A
browser-local `song_project_v1` owns the recording relationship and the master
timeline. The server receives musical timing and copedent context only; it does
not receive, store, inspect, identify, or log the recording.

Stage 1 is **Chord Karaoke**. Stages 2–5 remain unavailable until the preceding
stage has completed automated smoke and user smoke:

1. Chord Karaoke
2. Chord Moves
3. Answer the Singer
4. Take the Break
5. Carry the Melody

The fifth role is an alternative melody-feature performance. It does not add a
melody on top of the Level 4 solo.

## Feature gate

- Environment flag: `STEEL_RAG_ENABLE_SONG_PRACTICE`
- Default: off
- Session capability: `features.songPractice`
- The flag controls the Learn a song entry choice, pilot catalog, and arrange
  endpoint. It does not change the existing Melody Studio feature flags.

## Browser project contract

`song_project_v1` contains:

- `id`, `schemaVersion`, `createdAt`, and `updatedAt`
- key and meter
- chart mode (`letter` or `nashville`)
- sectioned measures and chord events
- captured bar timestamps and synchronization offset
- optional section cue phrases, each no longer than 80 characters
- role markers
- selected style and chosen plan
- either a built-in track ID or non-retained local-file identity
- provenance and version metadata

The local-file identity is limited to filename, byte size, last-modified time,
and measured duration. Audio bytes, object URLs, decoded samples, and media
blobs are forbidden in IndexedDB and JSON exports. Reopening a local project
requires the user to select the recording again. The browser checks all four
identity fields before accepting the relink.

## Chart and synchronization contract

- Letter charts and Nashville charts are explicit modes; a chart is never
  guessed between modes.
- Section markers use `[Section label]` followed by bar-delimited measures.
- A bar may contain multiple chords. Until manually reviewed, its chord events
  divide the bar evenly and carry `needsReview: true`.
- Invalid chord symbols block arrangement. Valid but unsupported qualities
  remain on the timeline with `manual_position_needed`; they never receive
  fabricated positions or tablature.
- Space captures each bar downbeat against the active audio element. Undo,
  per-bar nudge, section retap, global synchronization offset, seeking,
  looping, and playback-rate changes operate on the same timestamps.

## Arrange API

Authenticated endpoint:

```text
POST /api/song-practice/arrange
```

The request contains only:

```json
{
  "schemaVersion": "song_practice_request_v1",
  "level": "chord_karaoke",
  "key": "G",
  "meter": "4/4",
  "style": "classic_country",
  "events": [
    {
      "id": "chord-1",
      "measureId": "measure-1",
      "sectionId": "verse-1",
      "chord": "G",
      "startMs": 0,
      "endMs": 2400,
      "role": "comp"
    }
  ],
  "copedentContext": {
    "profileId": "emmons-e9-basic"
  }
}
```

The request rejects audio bytes, filename, song title, artist, and cue text.
The server resolves the existing copedent reference through the normal
authenticated copedent boundary.

The response is `song_practice_plan_v1` and contains:

- a canonical timeline hash
- one coherent recommended route across the complete chart
- timed performance events
- mechanically and pitch-validated positions
- exact-position alternatives
- `manual_position_needed` events for unsupported qualities
- warnings and deterministic provenance labels

Stage 1 never returns transition choreography, fills, solos, or melody events.

## Built-in track contract

The authenticated pilot catalog is sourced from a checked manifest. A catalog
item is exposed only when all of the following are present and valid:

- composition source and status
- arrangement owner and rights basis
- master owner and license/rights basis
- performer or generator credit
- SHA-256 checksum matching the tracked audio file
- duration, key, meter, synchronized bar map, and `noSteel: true`
- an audio file below the repository's 2 MiB tracked-file limit

The three Stage 1 pilots are Amazing Grace, When the Saints Go Marching In,
and Oh! Susanna. Generated preview masters remain internal-preview assets until
the exact manifest and masters receive public-launch rights review. A public-
domain composition never implies that an unrelated modern recording is free
to use.

## Deferred work

Stage 1 does not include automatic chord recognition, lyrics import, vocal
separation, solo transcription, title-only melody reconstruction, cloud
project sync, streaming-provider integration, scraping, corpus ingestion,
embeddings, Chroma changes, authentication-policy changes, or launch review of
the pilot masters.
