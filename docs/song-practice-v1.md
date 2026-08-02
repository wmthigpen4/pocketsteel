# Song Practice v1

## Product boundary

**Play Songs** is the dedicated performance path in Steel Guitar RAG. **Songs**
names the catalog and **Play Along** names synchronized playback. Melody Studio
remains the separate arrangement-authoring workspace.

A versioned `practice_project_v1` owns the recording relationship and master
timeline for bundled and local sources. The server receives musical timing and
copedent context only; it does not receive, store, inspect, identify, or log a
device-only recording.

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
- Default: on; an explicit false value disables the capability
- Session capability: `features.songPractice`
- The flag controls the Songs catalog and arrange endpoint. It does not change
  the existing Melody Studio feature flags.

## Navigation contract

- The app home keeps Fretboard Explorer, Melody Studio, Lessons, and Steel
  Guitar Q&A in their established order.
- A full-width Play Songs entry appears before those four cards.
- `/songs` lists curated lessons before device-only tracks.
- `/play/<projectId>` opens the dedicated landscape-first player.
- Back from Play Along returns to Songs; back from Songs returns home.

## Browser project contract

`practice_project_v1` contains:

- `id`, `schemaVersion`, `createdAt`, and `updatedAt`
- key and meter
- chart mode (`letter` or `nashville`)
- sectioned measures and chord events
- captured bar timestamps and synchronization offset
- optional section cue phrases, each no longer than 80 characters
- role markers
- selected style and chosen plan
- `audio.kind` of `bundled` or `local`
- confirmed beat/bar timestamps, meter, and timed chord cues
- synchronized sections and optional lyric cues
- a generated continuity-first E9 route and loop settings
- provenance and version metadata

Device audio is stored in the Origin Private File System. IndexedDB and JSON
exports contain metadata only. Imported audio is never sent in a network
request. The device library supports removal and metadata-only export; relink
and analysis/correction build on this same project contract.

## Learner path and advanced builder boundary

Chord Karaoke begins with a ready-to-play experience. For a built-in song, the
learner chooses the song and presses **Play song**. The track has a recognizable
public-domain melody lead, a one-bar count-in, quiet accompaniment, and a
reviewed synchronized chord map. The learner's only required job is to play the
chord shown on screen.

A local recording receives an automatic even-bar timing pass from its chart and
duration. That pass is intentionally described as a first pass, not automatic
audio analysis. Users who know the song may open **Edit synchronization
(advanced)** to replace bar starts, nudge timing, or repair drift. Downbeat
tapping is never a prerequisite for entry-level practice.

## Chart and synchronization contract

- Letter charts and Nashville charts are explicit modes; a chart is never
  guessed between modes.
- Section markers use `[Section label]` followed by bar-delimited measures.
- A bar may contain multiple chords. Until manually reviewed, its chord events
  divide the bar evenly and carry `needsReview: true`.
- Invalid chord symbols block arrangement. Valid but unsupported qualities
  remain on the timeline with `manual_position_needed`; they never receive
  fabricated positions or tablature.
- Built-in songs ship with reviewed bar timestamps and require no tapping.
- Local songs get an automatic even-bar first pass. The optional advanced
  editor lets Space replace bar downbeats; undo, per-bar nudge, section retap,
  global synchronization offset, seeking, looping, and playback-rate changes
  operate on the same timestamps.

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
- `melodyLead: true`, a positive count-in bar count, and `learnerReady: true`
- an audio file below the repository's 2 MiB tracked-file limit

The public Starter Songs registry contains published, playable lessons only.
Amazing Grace is the golden end-to-end fixture. When the Saints Go Marching In,
Hard Times Come Again No More, and future prospects remain in the non-public
candidate pipeline until screening, rights, master, timeline, E9 lesson, QA,
and publication gates have all passed. A public-domain composition never
implies that an unrelated modern recording is free to use.

The internal candidate and rights registries live under
`steel_guitar_rag/resources/song_catalog/`. Validate them and print the exact
next gate for every candidate with:

```bash
.venv/bin/python scripts/song_catalog_pipeline.py --check
```

Setting `learnerReady` in the audio manifest is insufficient. The public catalog
also requires a matching `published` candidate whose complete gate sequence and
publication-approved rights record validate successfully.

## Deferred work

Stage 1 does not include automatic chord recognition, lyrics import, vocal
separation, solo transcription, title-only melody reconstruction, cloud
project sync, streaming-provider integration, scraping, corpus ingestion,
embeddings, Chroma changes, authentication-policy changes, or launch review of
the pilot masters.
